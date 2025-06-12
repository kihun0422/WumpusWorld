from world import WumpusWorld
from agent import WumpusAgent
from ui import WumpusUI
import config # 추가

class WumpusGame:
    """개선된 Wumpus World 게임 컨트롤러"""
    
    def __init__(self):
        self.world = WumpusWorld()
        self.agent = WumpusAgent()
        self.ui = WumpusUI(self.agent, self.world)
        self.game_running = True # 게임 진행 상태
        self.is_auto_mode = False # 자동 모드 플래그
        
        # 초기 센서 정보 업데이트
        sensor_info = self.world.get_sensor_info(self.agent.x, self.agent.y)
        self.agent.update_knowledge(sensor_info)
        
        # UI 초기화
        self.ui.draw_all()
        self.ui.bind_keys(self.handle_input) # 키 바인딩
        self.ui.root.bind('<Return>', self.toggle_auto_mode) # Enter 키로 자동/수동 모드 전환
    
    def toggle_auto_mode(self, event=None):
        self.is_auto_mode = not self.is_auto_mode
        if self.is_auto_mode:
            print("자동 모드.")
            self.run_agent_turn() # 자동 모드 시작 시 첫 턴 실행
        else:
            print("수동 모드.")

    def run_agent_turn(self):
        if not self.game_running or not self.is_auto_mode:
            return

        action = self.agent.choose_action()
        self.execute_action(action)
        
        self.ui.draw_all()

        if self.game_running and self.is_auto_mode:
            self.ui.root.after(1000, self.run_agent_turn) # 1초 후 다음 턴 실행

    def execute_action(self, action_string):
        """choose_action에서 반환된 문자열에 따라 행동을 실행합니다."""
        if not self.game_running:
            return

        if action_string is None:
            print("에이전트가 행동을 결정하지 못했습니다.")
            return

        if action_string.startswith('MOVE_'):
            direction = action_string.split('_')[1]
            # agent.py의 move는 'UP','DOWN' 등을 직접 받음
            move_success = self.agent.move(direction)
            if move_success:
                sensor_info = self.world.get_sensor_info(self.agent.x, self.agent.y)
                self.agent.update_knowledge(sensor_info)
                self.check_hazards() # 이동 후 위험 체크
            else:
                # 벽에 부딪혔을 때 agent.py의 _discover_wall이 호출되고 지식 업데이트됨
                # 센서 정보 업데이트 (bump)
                current_pos_knowledge = self.agent.agent_knowledge.get((self.agent.x, self.agent.y), {})
                current_pos_knowledge['bump'] = True
                self.agent.agent_knowledge[(self.agent.x, self.agent.y)] = current_pos_knowledge
                # 추가적인 update_knowledge 호출은 상황에 따라 필요할 수 있음
                print(config.MESSAGES['actions']['wall_hit'])
        elif action_string.startswith('TURN_'):
            turn_direction = action_string.split('_')[1] # 'LEFT' 또는 'RIGHT'
            self.agent.turn(turn_direction)
            # 방향 전환 후 특별히 할 일은 없음. UI는 다음 턴에 어차피 그려짐.
        elif action_string == 'GRAB':
            self.grab_gold()
        elif action_string == 'SHOOT':
            self.shoot_arrow()
        elif action_string == 'CLIMB':
            self.climb()
        else:
            print(f"알 수 없는 행동: {action_string}")

    def handle_input(self, event):
        """키 입력 처리 (수동 모드용)"""
        if not self.game_running or self.is_auto_mode: # 자동 모드에서는 수동 입력 무시
            if event.keysym.lower() == 'r': # 리셋 키 (디버깅용)
                self.reset_game()
            return

        action_to_perform = None
        # config.KEY_MAPPING 사용
        key_action = config.KEY_MAPPING.get(event.keysym)
        if key_action in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            action_to_perform = f'MOVE_{key_action}' # choose_action의 반환 형식과 맞춤
        elif key_action == 'grab':
            action_to_perform = 'GRAB'
        elif key_action == 'shoot':
            action_to_perform = 'SHOOT'
        elif key_action == 'climb':
            action_to_perform = 'CLIMB'
        elif event.keysym.lower() == 'r': # 리셋 키
            self.reset_game()
            return

        if action_to_perform:
            self.execute_action(action_to_perform)
            self.ui.draw_all()
            
    def check_hazards(self):
        """현재 위치의 위험 요소 체크 및 사망/리스폰 처리"""
        if not self.game_running: return

        current_pos = (self.agent.x, self.agent.y)
        died = False
        death_message = ""

        if current_pos in self.world.wumpus_positions:
            death_message = config.MESSAGES['game_over']['wumpus']
            # 에이전트 지식에 Wumpus 확정 정보 기록
            if current_pos not in self.agent.agent_knowledge:
                self.agent.agent_knowledge[current_pos] = self.world.get_sensor_info(current_pos[0], current_pos[1])
            else:
                # sensor_info 에서 wumpus, pitch 정보만 가져와서 업데이트 할 수도 있음.
                # 여기서는 world 에서 직접 wumpus 정보를 가져와 덮어쓰기.
                self.agent.agent_knowledge[current_pos]['wumpus'] = True 
            self.agent.agent_knowledge[current_pos]['pitch'] = False # Wumpus가 있으면 Pitch는 없음 (일반적 가정)
            self.agent.confirmed_wumpuses.add(current_pos)
            self.agent.wumpus_candidates.discard(current_pos)
            # 다른 후보지/확정지에서 이 위치를 제거
            self.agent.confirmed_pitches.discard(current_pos)
            self.agent.pitch_candidates.discard(current_pos)
            died = True
        
        if not died and current_pos in self.world.pitch_positions:
            death_message = config.MESSAGES['game_over']['pitch']
            # 에이전트 지식에 Pitch 확정 정보 기록
            if current_pos not in self.agent.agent_knowledge:
                self.agent.agent_knowledge[current_pos] = self.world.get_sensor_info(current_pos[0], current_pos[1])
            else:
                self.agent.agent_knowledge[current_pos]['pitch'] = True
            self.agent.agent_knowledge[current_pos]['wumpus'] = False # Pitch가 있으면 Wumpus는 없음
            self.agent.confirmed_pitches.add(current_pos)
            self.agent.pitch_candidates.discard(current_pos)
            # 다른 후보지/확정지에서 이 위치를 제거
            self.agent.confirmed_wumpuses.discard(current_pos)
            self.agent.wumpus_candidates.discard(current_pos)
            died = True
        
        if died:
            self.ui.draw_all() # 사망 상태(확정된 Wumpus/Pit)를 UI에 먼저 그리고 리스폰 처리
            self.agent.reset_for_respawn() # 에이전트 상태 리셋 (지식 유지, 화살 리필 등)
            # 월드의 위험요소(Wumpus, Pit)는 그대로 유지 (달라지지 않음)
            # 금의 위치도 그대로 유지 (만약 에이전트가 금을 가지고 있었다면 리스폰 시 잃음)
            print("에이전트가 사망하여 (1,1)에서 리스폰합니다.")
            sensor_info = self.world.get_sensor_info(self.agent.x, self.agent.y)
            self.agent.update_knowledge(sensor_info) # 리스폰 위치에서의 센서 정보로 업데이트
            self.ui.draw_all()
            # 게임을 계속 진행 (game_running = True 유지)
        else:
            # 생존 시 아무것도 하지 않음 (또는 점수 증가 등)
            pass

    def grab_gold(self):
        """금 획득 처리"""
        if not self.game_running: return
        current_pos = (self.agent.x, self.agent.y)
        
        # world.collect_gold는 금이 있으면 True 반환하고 금을 제거함
        if self.world.collect_gold(current_pos):
            # agent.grab_gold는 glitter를 보고 has_gold를 True로 바꿈
            if self.agent.grab_gold(): # 에이전트 지식상 glitter가 있어야 함
                print(config.MESSAGES['actions']['gold_collected'])
            else:
                self.agent.has_gold = True # 강제 획득 처리
    
    def shoot_arrow(self):
        """개선된 화살 발사 처리"""
        if not self.game_running: return

        if self.agent.arrows <= 0:
            print(config.MESSAGES['actions']['no_arrows'])
            # self.ui.draw_all() # execute_action에서 호출됨
            return
        
        hit_wumpus_pos = self.agent.shoot_arrow(self.world) # world 객체를 넘겨줌
        
        # 화살 발사 후 현재 위치의 센서 정보를 **무조건** 다시 수집
        # Wumpus가 죽으면 Stench가 사라질 수 있으므로 중요
        current_sensor_info = self.world.get_sensor_info(self.agent.x, self.agent.y)
        
        print(f"화살 발사 후 ({self.agent.x},{self.agent.y})에서 센서 정보 재인지 및 추론 실행")
        self.agent.update_knowledge(current_sensor_info)
        
        if hit_wumpus_pos:
            print(config.MESSAGES['actions']['wumpus_killed']) # agent.py 내부에서도 Scream 출력함
            # Wumpus가 죽었으므로, UI에 반영될 수 있도록 해당 Wumpus 위치 정보를 world에서 제거하는 것은
            # agent.shoot_arrow 내부의 world.remove_wumpus(pos)가 담당.
        else:
            print(config.MESSAGES['actions']['arrow_miss'])
    
    def climb(self):
        """탈출 처리"""
        if not self.game_running: return

        if self.agent.can_climb(): # (1,1)이고 금을 가지고 있는지 확인
            print(config.MESSAGES['game_over']['success'])
            self.game_over(config.MESSAGES['game_over']['success'], success=True)
        else:
            if (self.agent.x, self.agent.y) != (1, 1):
                print(config.MESSAGES['actions']['climb_wrong_position'])
            elif not self.agent.has_gold:
                print(config.MESSAGES['actions']['climb_no_gold'])
    
    def game_over(self, message, success=False):
        if success:
            self.game_running = False # 게임 루프 중단
            self.is_auto_mode = False # 자동 모드 중단

    def reset_game(self):
        self.world.reset_world() # 월드 (Wumpus, Pit, Gold) 재배치
        self.agent = WumpusAgent() # 에이전트 새로 생성 (모든 지식 초기화)
        self.ui.agent = self.agent # UI가 새 에이전트 참조하도록 업데이트
        self.ui.world = self.world # UI가 새 월드 참조하도록 업데이트
        
        sensor_info = self.world.get_sensor_info(self.agent.x, self.agent.y)
        self.agent.update_knowledge(sensor_info)
        
        self.game_running = True
        self.is_auto_mode = False # 수동 모드로 시작
        self.ui.draw_all()
    
    def run(self):
        self.ui.run() # Tkinter mainloop 시작

# 게임 실행
if __name__ == "__main__":
    game = WumpusGame()
    game.run()