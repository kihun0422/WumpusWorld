import random
import config # config.py 임포트
from itertools import combinations, chain # itertools 임포트 위치 변경
import collections # BFS를 위한 deque 임포트

class WumpusAgent:
    """개선된 Wumpus World 에이전트 클래스"""
    
    def __init__(self):
        self.x = 1 
        self.y = 1 
        self.direction = config.INITIAL_DIRECTION
        self.arrows = config.INITIAL_ARROWS 
        self.has_gold = False
        self.map_size = (config.BOARD_SIZE, config.BOARD_SIZE)

        self.visited = set()
        self.visited.add((self.x, self.y)) 
        self.agent_knowledge = {}  
        self.wumpus_candidates = set()
        self.pitch_candidates = set()
        self.discovered_walls = set()  
        self.confirmed_wumpuses = set()  
        self.confirmed_pitches = set()  
        self.just_bumped = False # 직전에 벽에 부딪혔는지 여부
        self.last_bumped_direction = None # 직전에 부딪힌 방향
        self.previous_pos = None # 직전 위치 (무한 루프 방지용)
        
        # UP, RIGHT, DOWN, LEFT 순서 (시계 방향)
        self.direction_order = ['UP', 'RIGHT', 'DOWN', 'LEFT']
        
        self.agent_knowledge[(self.x,self.y)] = {
            'stench': None, 'breeze': None, 'glitter': None, 'wall': False,
            'wumpus': False, 'pitch': False, 'bump': False
        }
    
    def move(self, direction):
        """에이전트 이동 (성공 여부 반환)"""
        new_x, new_y = self.x, self.y
        
        # 먼저 에이전트의 현재 방향을 설정
        self.direction = direction 
        
        if direction == 'UP':
            new_y += 1
        elif direction == 'DOWN':
            new_y -= 1
        elif direction == 'LEFT':
            new_x -= 1
        elif direction == 'RIGHT':
            new_x += 1
        
        # 현재 위치의 bump 정보 초기화 (이동 시도 전)
        if (self.x,self.y) in self.agent_knowledge:
            self.agent_knowledge[(self.x,self.y)]['bump'] = False
        self.just_bumped = False
        self.last_bumped_direction = None

        # 이동 직전에 현재 위치를 previous_pos로 기록
        self.previous_pos = (self.x, self.y) # 이동 성공 직전에 기록

        if 1 <= new_x <= self.map_size[0] and 1 <= new_y <= self.map_size[1] and \
           (new_x, new_y) not in self.discovered_walls : # 실제 벽으로 이동하는지 확인
            self.x, self.y = new_x, new_y
            self.visited.add((new_x, new_y))
            return True
        else:
            self._discover_wall(direction) # 여기서 self.just_bumped = True 설정됨
            return False
    
    def _discover_wall(self, direction):
        """벽 발견 처리"""
        current_info = self.agent_knowledge.get((self.x, self.y), {})
        current_info['bump'] = True
        self.agent_knowledge[(self.x, self.y)] = current_info
        self.just_bumped = True 
        self.last_bumped_direction = direction # 부딪힌 방향 기록
        
        actual_wall_coord = None
        if direction == 'UP': actual_wall_coord = (self.x, self.y + 1)
        elif direction == 'DOWN': actual_wall_coord = (self.x, self.y - 1)
        elif direction == 'LEFT': actual_wall_coord = (self.x - 1, self.y)
        elif direction == 'RIGHT': actual_wall_coord = (self.x + 1, self.y)

        if actual_wall_coord:
            self.discovered_walls.add(actual_wall_coord)
    
    def turn(self, turn_direction):
        """에이전트 방향 전환 (제자리 회전)"""
        current_idx = self.direction_order.index(self.direction)
        if turn_direction == 'LEFT':
            new_idx = (current_idx - 1 + 4) % 4
        elif turn_direction == 'RIGHT':
            new_idx = (current_idx + 1) % 4
        else:
            return # 유효하지 않은 입력

        self.direction = self.direction_order[new_idx]
        
        # 회전은 이동이 아니므로, bump 상태 등을 초기화합니다.
        if (self.x,self.y) in self.agent_knowledge:
            self.agent_knowledge[(self.x,self.y)]['bump'] = False
        self.just_bumped = False
        self.last_bumped_direction = None
        return True
    
    def grab_gold(self):
        """금 획득 시도"""
        current_info = self.agent_knowledge.get((self.x, self.y), {})
        if current_info.get('glitter', False):
            self.has_gold = True
            current_info['bump'] = False
            self.agent_knowledge[(self.x,self.y)] = current_info
            self.just_bumped = False
            self.last_bumped_direction = None
            return True
        return False
    
    def shoot_arrow(self, world):
        """화살 발사 - 개선된 버전 (첫 번째 Wumpus만 제거)"""
        if self.arrows <= 0:
            return False
        
        self.arrows -= 1
        self.just_bumped = False # 행동 수행 시 bump 상태 초기화
        self.last_bumped_direction = None
        
        arrow_path = self._get_arrow_path()
        hit_position = None
        
        for pos in arrow_path:
            if pos in world.wumpus_positions:
                world.remove_wumpus(pos)
                hit_position = pos
                break
        
        if hit_position:
            self._process_arrow_hit(arrow_path, hit_position)
        else:
            self._process_arrow_miss(arrow_path)
        
        return hit_position is not None
    
    def _get_arrow_path(self, direction_to_check=None, from_pos=None):
        """화살이 지나가는 경로 계산 (순서대로). direction_to_check가 없으면 self.direction 사용."""
        path = []
        current_x, current_y = from_pos if from_pos else (self.x, self.y)
        arrow_direction = direction_to_check if direction_to_check else self.direction
        
        if arrow_direction == 'RIGHT':
            for x_coord in range(current_x + 1, self.map_size[0] + 1):
                if (x_coord, current_y) in self.discovered_walls: break
                path.append((x_coord, current_y))
        elif arrow_direction == 'LEFT':
            for x_coord in range(current_x - 1, 0, -1):
                if (x_coord, current_y) in self.discovered_walls: break
                path.append((x_coord, current_y))
        elif arrow_direction == 'UP':
            for y_coord in range(current_y + 1, self.map_size[1] + 1):
                if (current_x, y_coord) in self.discovered_walls: break
                path.append((current_x, y_coord))
        elif arrow_direction == 'DOWN':
            for y_coord in range(current_y - 1, 0, -1):
                if (current_x, y_coord) in self.discovered_walls: break
                path.append((current_x, y_coord))
        
        return path

    def _process_arrow_hit(self, arrow_path, hit_position):
        """화살이 명중했을 때의 처리 (Scream 발생) - 하나의 Wumpus만 처리"""
        if hit_position in self.confirmed_wumpuses:
            self.confirmed_wumpuses.remove(hit_position)
        
        self.wumpus_candidates.discard(hit_position)
        
        if hit_position not in self.agent_knowledge:
            self.agent_knowledge[hit_position] = {
                'stench': False, 'breeze': False, 'glitter': False, 'wall': False,
                'wumpus': None, 'pitch': None, 'bump': False
            }
        self.agent_knowledge[hit_position]['wumpus'] = False
        
        hit_index = arrow_path.index(hit_position)
        path_before_hit = arrow_path[:hit_index]
        
        for pos in path_before_hit:
            if pos in self.wumpus_candidates:
                self.wumpus_candidates.remove(pos)
            if pos not in self.agent_knowledge:
                self.agent_knowledge[pos] = {
                    'stench': False, 'breeze': False, 'glitter': False, 'wall': False,
                    'wumpus': False, 'pitch': None, 'bump': False
                }
            else:
                self.agent_knowledge[pos]['wumpus'] = False
                self.agent_knowledge[pos]['stench'] = False 
    
    def _process_arrow_miss(self, arrow_path):
        """화살이 빗나갔을 때의 처리 (Scream 없음)"""
        removed_candidates = []
        for pos in arrow_path:
            if pos in self.wumpus_candidates:
                self.wumpus_candidates.remove(pos)
                removed_candidates.append(pos)
                if pos not in self.agent_knowledge:
                    self.agent_knowledge[pos] = {
                        'stench': False, 'breeze': False, 'glitter': False, 'wall': False,
                        'wumpus': None, 'pitch': None, 'bump': False
                    }
                self.agent_knowledge[pos]['wumpus'] = False
        
        if removed_candidates:
            pass
    
    def _recalculate_sensor_implications(self):
        """센서 정보의 함의 재계산"""
        self._clean_invalid_candidates()
        for visited_pos in self.visited:
            sensor_info = self.agent_knowledge.get(visited_pos, {})
            if sensor_info.get('stench', False):
                explaining_wumpus = self._get_confirmed_wumpus_for_position(*visited_pos)
                if not explaining_wumpus:
                    self._add_missing_wumpus_candidates(visited_pos)
            if sensor_info.get('breeze', False):
                explaining_pitch = self._get_confirmed_pitch_for_position(*visited_pos)
                if not explaining_pitch:
                    self._add_missing_pitch_candidates(visited_pos)
    
    def _add_missing_wumpus_candidates(self, visited_pos):
        x, y = visited_pos
        adjacent = self._get_adjacent_positions(x, y)
        for ax, ay in adjacent:
            if (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1] and 
                (ax, ay) not in self.visited and (ax, ay) not in self.discovered_walls and
                (ax, ay) not in self.confirmed_pitches):
                adjacent_info = self.agent_knowledge.get((ax, ay), {})
                if adjacent_info.get('wumpus') != False:
                    self.wumpus_candidates.add((ax, ay))
    
    def _add_missing_pitch_candidates(self, visited_pos):
        x, y = visited_pos
        adjacent = self._get_adjacent_positions(x, y)
        for ax, ay in adjacent:
            if (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1] and 
                (ax, ay) not in self.visited and (ax, ay) not in self.discovered_walls and
                (ax, ay) not in self.confirmed_wumpuses):
                adjacent_info = self.agent_knowledge.get((ax, ay), {})
                if adjacent_info.get('pitch') != False:
                    self.pitch_candidates.add((ax, ay))
    
    def can_climb(self):
        """탈출 가능한지 확인"""
        return (self.x, self.y) == (1, 1) and self.has_gold
    
    def update_knowledge(self, sensor_info):
        """센서 정보를 바탕으로 지식 업데이트"""
        current_pos = (self.x, self.y)
        if current_pos not in self.agent_knowledge:
             self.agent_knowledge[current_pos] = {}
        
        preserved_bump = self.agent_knowledge[current_pos].get('bump', False)
        self.agent_knowledge[current_pos] = sensor_info.copy()
        if self.just_bumped :
             self.agent_knowledge[current_pos]['bump'] = True
        else:
             self.agent_knowledge[current_pos]['bump'] = False


        self._update_certain_info(self.x, self.y, sensor_info)
        self._update_candidates(self.x, self.y, sensor_info)
        self._advanced_deduction()
    
    def _update_certain_info(self, x, y, sensor_info):
        """센서 정보를 바탕으로 인접 위치의 확실한 정보 업데이트"""
        adjacent = self._get_adjacent_positions(x, y)
        
        for ax, ay in adjacent:
            if 1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1]:
                if (ax, ay) not in self.agent_knowledge:
                    self.agent_knowledge[(ax, ay)] = {
                        'stench': None, 'breeze': None, 'glitter': None, 'wall': False,
                        'wumpus': None, 'pitch': None, 'bump': False 
                    }
                
                adj_cell_knowledge = self.agent_knowledge[(ax, ay)]
                
                if (ax, ay) in self.visited or (ax,ay) in self.discovered_walls: 
                    continue
                
                if not sensor_info.get('stench', False): 
                    if adj_cell_knowledge.get('wumpus') is None: 
                        adj_cell_knowledge['wumpus'] = False
                
                if not sensor_info.get('breeze', False): 
                    if adj_cell_knowledge.get('pitch') is None: 
                        adj_cell_knowledge['pitch'] = False
    
    def _update_candidates(self, x, y, sensor_info):
        """후보 위치 업데이트"""
        adjacent = self._get_adjacent_positions(x, y)
        
        if sensor_info.get('stench', False):
            for ax, ay in adjacent:
                if (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1] and 
                    (ax, ay) not in self.visited and (ax,ay) not in self.discovered_walls and
                    (ax, ay) not in self.confirmed_pitches):
                    adjacent_info = self.agent_knowledge.get((ax, ay), {})
                    if adjacent_info.get('wumpus') != False:
                        self.wumpus_candidates.add((ax, ay))
        
        if sensor_info.get('breeze', False):
            for ax, ay in adjacent:
                if (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1] and 
                    (ax, ay) not in self.visited and (ax,ay) not in self.discovered_walls and
                    (ax, ay) not in self.confirmed_wumpuses):
                    adjacent_info = self.agent_knowledge.get((ax, ay), {})
                    if adjacent_info.get('pitch') != False:
                        self.pitch_candidates.add((ax, ay))
        
        self._clean_invalid_candidates()

    def _advanced_deduction(self):
        """개선된 추론 시스템 - 모든 가능한 조합을 검증"""
        self._find_definitive_positions()
        self._constraint_based_reasoning()
        self._verify_all_consistency()
    
    def _find_definitive_positions(self):
        # 에이전트가 방문했던 모든 위치를 순회하며,
        # 각 위치의 센서 정보로부터 단일 원인으로 위험(Wumpus/Pit)을 확정할 수 있는지 검사합니다.
        for visited_pos in self.visited:
            self._check_single_cause_positions(visited_pos)
    
    def _check_single_cause_positions(self, visited_pos):
        # 특정 방문 위치(visited_pos)의 센서 정보를 기반으로 단일 원인 분석을 수행하여 Wumpus 또는 Pit을 확정합니다.
        # 예를 들어, visited_pos에서 stench가 났고, 이 stench의 원인이 될 수 있는 인접 미탐험 칸이 단 하나뿐이며,
        # 다른 정보와 모순되지 않는다면, 그 유일한 칸을 Wumpus로 확정합니다.
        x, y = visited_pos
        sensor_info = self.agent_knowledge.get(visited_pos, {}) # 해당 위치의 센서 정보
        
        # 1. stench(Stench)가 감지된 경우 Wumpus 확정 시도
        if sensor_info.get('stench', False):
            # visited_pos 주변의 Wumpus 후보 칸들을 가져옵니다.
            possible_wumpus = self._get_possible_wumpus_for_position(x, y)
            # visited_pos 주변의 이미 확정된 Wumpus 칸들을 가져옵니다.
            confirmed_wumpus_explaining = self._get_confirmed_wumpus_for_position(x, y)
            
            # 만약, 현재 stench를 설명할 수 있는 '이미 확정된' Wumpus가 주변에 없고,
            # stench의 원인이 될 수 있는 '후보' Wumpus 칸이 '단 하나' 뿐이라면,
            if not confirmed_wumpus_explaining and len(possible_wumpus) == 1:
                new_wumpus = possible_wumpus.pop() # 유일한 Wumpus 후보
                # 이 후보를 Wumpus로 가정했을 때 전체 지식과 모순이 없는지 테스트.
                if self._test_wumpus_consistency(new_wumpus):
                    # 모순이 없다면, 해당 후보를 Wumpus로 확정
                    self._confirm_wumpus(new_wumpus)
        
        # 2. breeze(Breeze)이 감지된 경우 Pit 확정 시도
        if sensor_info.get('breeze', False):
            # visited_pos 주변의 Pit 후보 칸들을 가져옵니다.
            possible_pitch = self._get_possible_pitch_for_position(x, y)
            # visited_pos 주변의 이미 확정된 Pit 칸들을 가져옵니다.
            confirmed_pitch_explaining = self._get_confirmed_pitch_for_position(x, y)
            
            # 만약, 현재 breeze을 설명할 수 있는 '이미 확정된' Pit이 주변에 없고,
            # breeze의 원인이 될 수 있는 '후보' Pit 칸이 단 하나 뿐이라면,
            if not confirmed_pitch_explaining and len(possible_pitch) == 1:
                new_pitch = possible_pitch.pop() # 유일한 Pit 후보
                # 이 후보를 Pit으로 가정했을 때 전체 지식과 모순이 없는지 테스트.
                if self._test_pitch_consistency(new_pitch):
                    # 모순이 없다면, 해당 후보를 Pit으로 확정.
                    self._confirm_pitch(new_pitch)

    def _constraint_based_reasoning(self):
        # 제약 조건 기반 추론: Wumpus와 Pit의 위치를 확정하기 위해 가능한 모든 조합을 생성하고 검증합니다.
        # 1. Wumpus 추론:
        #   a. 현재 Wumpus 후보들과 이미 확정된 Wumpus들을 조합하여 가능한 모든 Wumpus 배치 시나리오를 생성.
        #   b. 각 시나리오가 지금까지 방문한 모든 위치의 stench(stench) 정보와 일관되는지 테스트.
        #   c. 모든 일관된 시나리오에서 공통적으로 Wumpus가 존재한다고 나타나는 위치를 Wumpus로 확정.
        
        # Wumpus 후보 조합 생성
        wumpus_combinations = self._generate_wumpus_combinations()
        valid_wumpus_combinations = [] # 일관성이 확인된 Wumpus 조합(시나리오)들을 저장할 리스트
        # 각 Wumpus 조합에 대해 일관성 테스트
        for combination in wumpus_combinations:
            if self._test_wumpus_combination_consistency(combination):
                valid_wumpus_combinations.append(combination)
        
        # 유효한 Wumpus 조합들이 있다면, 공통적으로 Wumpus가 나타나는 위치를 확정
        if valid_wumpus_combinations:
            # 첫 번째 유효한 조합을 기준으로 초기 공통 Wumpus 집합 설정
            common_wumpus = set(valid_wumpus_combinations[0]) if valid_wumpus_combinations else set()
            # 나머지 유효한 조합들과의 교집합을 통해 공통 Wumpus 업데이트
            for combination in valid_wumpus_combinations[1:]:
                common_wumpus &= set(combination)
            # 공통적으로 나타난 Wumpus 위치들을 확정
            for pos in common_wumpus:
                if pos not in self.confirmed_wumpuses: # 아직 확정되지 않았다면
                    self._confirm_wumpus(pos)
        
        # 2. Pit 추론 (Wumpus와 동일한 로직 적용):
        #   a. 현재 Pit 후보들과 이미 확정된 Pit들을 조합하여 가능한 모든 Pit 배치 시나리오를 생성.
        #   b. 각 시나리오가 지금까지 방문한 모든 위치의 breeze 정보와 일관되는지 테스트.
        #   c. 모든 일관된 시나리오에서 공통적으로 Pit이 존재한다고 나타나는 위치를 Pit으로 확정.
        
        # Pit 후보 조합 생성
        pitch_combinations = self._generate_pitch_combinations()
        valid_pitch_combinations = [] # 일관성이 확인된 Pit 조합(시나리오)들을 저장할 리스트
        # 각 Pit 조합에 대해 일관성 테스트
        for combination in pitch_combinations:
            if self._test_pitch_combination_consistency(combination):
                valid_pitch_combinations.append(combination)

        # 유효한 Pit 조합들이 있다면, 공통적으로 Pit이 나타나는 위치를 확정
        if valid_pitch_combinations:
            # 첫 번째 유효한 조합을 기준으로 초기 공통 Pit 집합 설정
            common_pitch = set(valid_pitch_combinations[0]) if valid_pitch_combinations else set()
            # 나머지 유효한 조합들과의 교집합을 통해 공통 Pit 업데이트
            for i, combination in enumerate(valid_pitch_combinations[1:]):
                common_pitch &= set(combination)
            
            # 공통적으로 나타난 Pit 위치들을 확정
            for pos in common_pitch:
                if pos not in self.confirmed_pitches: # 아직 확정되지 않았다면
                    self._confirm_pitch(pos)

    def _generate_wumpus_combinations(self):
        candidates = list(self.wumpus_candidates - self.confirmed_wumpuses)
        all_combinations = []
        for r in range(len(candidates) + 1):
            for combo in combinations(candidates, r):
                full_combo = list(self.confirmed_wumpuses) + list(combo)
                all_combinations.append(full_combo)
        return all_combinations if all_combinations else [list(self.confirmed_wumpuses)]

    def _generate_pitch_combinations(self):
        candidates = list(self.pitch_candidates - self.confirmed_pitches)
        all_combinations = []
        for r in range(len(candidates) + 1):
            for combo in combinations(candidates, r):
                full_combo = list(self.confirmed_pitches) + list(combo)
                all_combinations.append(full_combo)
        return all_combinations if all_combinations else [list(self.confirmed_pitches)]

    def _test_wumpus_combination_consistency(self, wumpus_positions):
        # 주어진 Wumpus들의 위치(wumpus_positions) 가설이 에이전트가 방문했던 모든 칸의 실제 stench 정보와 일관되는지 검사.
        # 각 방문했던 칸에서, wumpus_positions에 따라 예상되는 stench와 실제 감지된 stench가 동일해야함.
        for visited_pos in self.visited: # 에이전트가 방문했던 모든 칸에 대해 반복
            vx, vy = visited_pos
            # 해당 방문 칸에서 실제 감지했던 stench 정보
            actual_stench = self.agent_knowledge.get(visited_pos, {}).get('stench', False)
            # wumpus_positions 가설에 따르면 해당 방문 칸에서 예상되는 stench
            # (인접한 칸에 wumpus_positions의 Wumpus가 하나라도 있으면 True)
            expected_stench = any(abs(wx - vx) + abs(wy - vy) == 1 for wx, wy in wumpus_positions)
            
            # 실제 stench와 예상 stench가 다르면, 이 Wumpus 조합은 일관성이 없으므로 False 반환
            if actual_stench != expected_stench:
                return False
        # 모든 방문한 칸에 stench 정보가 일관되면 True 반환
        return True

    def _test_pitch_combination_consistency(self, pitch_positions):
        # 주어진 Pit들의 위치(pitch_positions) 가설이 에이전트가 방문했던 모든 칸의 실제 breeze 정보와 일관되는지 검사.
        # 즉, 각 방문했던 칸에서, pitch_positions에 따라 예상되는 breeze과 실제 감지된 breeze이 동일해야 함.
        for visited_pos in self.visited: # 에이전트가 방문했던 모든 칸에 대해 반복
            vx, vy = visited_pos
            # 해당 방문 칸에서 실제 감지했던 breeze 정보
            actual_breeze = self.agent_knowledge.get(visited_pos, {}).get('breeze', False)
            # pitch_positions 가설에 따르면 해당 방문 칸에서 예상되는 breeze
            # (인접한 칸에 pitch_positions의 Pit이 하나라도 있으면 True)
            expected_breeze = any(abs(px - vx) + abs(py - vy) == 1 for px, py in pitch_positions)
            
            # 실제 breeze과 예상 breeze이 다르면, 이 Pit 조합은 일관성이 없으므로 False 반환
            if actual_breeze != expected_breeze:
                return False
        # 모든 방문한 칸에서 breeze 정보가 일관되면 True 반환
        return True

    def _get_possible_wumpus_for_position(self, x, y):
        possible = set()
        for ax, ay in self._get_adjacent_positions(x, y):
            if (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1] and 
                (ax, ay) not in self.visited and (ax,ay) not in self.discovered_walls and
                (ax, ay) in self.wumpus_candidates):
                possible.add((ax, ay))
        return possible

    def _get_possible_pitch_for_position(self, x, y):
        possible = set()
        for ax, ay in self._get_adjacent_positions(x, y):
            if (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1] and 
                (ax, ay) not in self.visited and (ax,ay) not in self.discovered_walls and
                (ax, ay) in self.pitch_candidates):
                possible.add((ax, ay))
        return possible

    def _get_confirmed_wumpus_for_position(self, x, y):
        confirmed = set()
        for ax, ay in self._get_adjacent_positions(x, y):
            if (ax, ay) in self.confirmed_wumpuses: confirmed.add((ax, ay))
        return confirmed

    def _get_confirmed_pitch_for_position(self, x, y):
        confirmed = set()
        for ax, ay in self._get_adjacent_positions(x, y):
            if (ax, ay) in self.confirmed_pitches: confirmed.add((ax, ay))
        return confirmed

    def _test_wumpus_consistency(self, wumpus_pos_to_test):
        if not isinstance(wumpus_pos_to_test, tuple): return False
        
        temp_confirmed_wumpuses = list(self.confirmed_wumpuses | {wumpus_pos_to_test})
        return self._test_wumpus_combination_consistency(temp_confirmed_wumpuses)

    def _test_pitch_consistency(self, pitch_pos_to_test):
        if not isinstance(pitch_pos_to_test, tuple): return False

        temp_confirmed_pitches = list(self.confirmed_pitches | {pitch_pos_to_test})
        return self._test_pitch_combination_consistency(temp_confirmed_pitches)
    
    def _confirm_wumpus(self, pos):
        self.confirmed_wumpuses.add(pos)
        self.wumpus_candidates.discard(pos)
        self.pitch_candidates.discard(pos) # Wumpus here means no Pit
        self.confirmed_pitches.discard(pos) # Also remove from confirmed Pits if it was somehow there
        if pos not in self.agent_knowledge:
            self.agent_knowledge[pos] = { 'stench': True, 'breeze': None, 'glitter': None, 'wall': False, 
                                          'wumpus': True, 'pitch': False, 'bump': False }
        else:
            self.agent_knowledge[pos]['wumpus'] = True
            self.agent_knowledge[pos]['pitch'] = False
            self.agent_knowledge[pos]['stench'] = True # Should sense stench if wumpus is confirmed here (even if agent not on it)
    
    def _confirm_pitch(self, pos):
        self.confirmed_pitches.add(pos)
        self.pitch_candidates.discard(pos)
        self.wumpus_candidates.discard(pos) # Pit here means no Wumpus
        self.confirmed_wumpuses.discard(pos) # Also remove from confirmed Wumpuses
        if pos not in self.agent_knowledge:
            self.agent_knowledge[pos] = { 'stench': None, 'breeze': True, 'glitter': None, 'wall': False, 
                                          'wumpus': False, 'pitch': True, 'bump': False }
        else:
            self.agent_knowledge[pos]['pitch'] = True
            self.agent_knowledge[pos]['wumpus'] = False
            self.agent_knowledge[pos]['breeze'] = True

    def _verify_all_consistency(self):
        wumpuses_to_demote = set()
        for visited_pos in self.visited:
            # 현재 에이전트 위치는 방금 센서로 직접 인지했으므로, 
            # 이 위치의 Wumpus/Pit 상태를 간접적인 주변 정보로 바꾸지 않도록 함.
            if visited_pos == (self.x, self.y):
                continue

            vx, vy = visited_pos
            actual_stench = self.agent_knowledge.get(visited_pos, {}).get('stench', False)
            if not actual_stench: 
                for adj_pos in self._get_adjacent_positions(vx, vy):
                    if 1 <= adj_pos[0] <= self.map_size[0] and 1 <= adj_pos[1] <= self.map_size[1]:
                        if adj_pos in self.confirmed_wumpuses:
                            # 만약 demote하려는 wumpus가 현재 에이전트 위치라면, 이는 직접 감지된 정보이므로 demote하지 않음
                            if adj_pos == (self.x, self.y) and self.agent_knowledge.get(adj_pos, {}).get('wumpus') is True:
                                continue
                            wumpuses_to_demote.add(adj_pos)
        
        if wumpuses_to_demote:
            for pos_to_demote in wumpuses_to_demote:
                # 현재 위치는 롤백 대상에서 제외 (이미 위에서 처리했어야 하지만, 이중 방어)
                if pos_to_demote == (self.x, self.y) and self.agent_knowledge.get(pos_to_demote, {}).get('wumpus') is True:
                    continue
                self.confirmed_wumpuses.discard(pos_to_demote)
                self.wumpus_candidates.add(pos_to_demote) 
                if pos_to_demote in self.agent_knowledge:
                    self.agent_knowledge[pos_to_demote]['wumpus'] = None 
                    self.agent_knowledge[pos_to_demote]['stench'] = None 

        pitches_to_demote = set()
        for visited_pos in self.visited:
            if visited_pos == (self.x, self.y):
                continue

            vx, vy = visited_pos
            actual_breeze = self.agent_knowledge.get(visited_pos, {}).get('breeze', False)
            if not actual_breeze: 
                for adj_pos in self._get_adjacent_positions(vx, vy):
                    if 1 <= adj_pos[0] <= self.map_size[0] and 1 <= adj_pos[1] <= self.map_size[1]:
                        if adj_pos in self.confirmed_pitches:
                            if adj_pos == (self.x, self.y) and self.agent_knowledge.get(adj_pos, {}).get('pitch') is True:
                                continue
                            pitches_to_demote.add(adj_pos)
        
        if pitches_to_demote:
            for pos_to_demote in pitches_to_demote:
                if pos_to_demote == (self.x, self.y) and self.agent_knowledge.get(pos_to_demote, {}).get('pitch') is True:
                    continue
                self.confirmed_pitches.discard(pos_to_demote)
                self.pitch_candidates.add(pos_to_demote) 
                if pos_to_demote in self.agent_knowledge:
                    self.agent_knowledge[pos_to_demote]['pitch'] = None 
                    self.agent_knowledge[pos_to_demote]['breeze'] = None

    def _clean_invalid_candidates(self):
        # 방문했다는 이유만으로 후보에서 제외하지 않도록.
        # 확실히 안전하거나 다른 위험이 확정된 경우에만 제외.
        self.wumpus_candidates -= (self.confirmed_pitches | self.confirmed_wumpuses | self.discovered_walls)
        self.pitch_candidates -= (self.confirmed_wumpuses | self.confirmed_pitches | self.discovered_walls)

        # 에이전트 지식에 확실히 안전하다고 기록된 후보들을 제거
        w_safe_to_remove = {c for c in self.wumpus_candidates if self.agent_knowledge.get(c, {}).get('wumpus') is False}
        p_safe_to_remove = {c for c in self.pitch_candidates if self.agent_knowledge.get(c, {}).get('pitch') is False}
        
        # 방문한 위치 중, 센서 정보로 인해 안전하다고 추론된 곳도 제거
        # ex. (x,y)를 방문했고, 그곳에 stench가 없었다면, 인접한 칸들은 wumpus 후보에서 제거될 수 있음.
        # 이 로직은 _update_certain_info 에서 이미 처리되므로, 여기서는 agent_knowledge의 False 상태만 봐도 추론 가능.
        # 하지만, 확실하게 하기 위해 visited에 있고, agent_knowledge에 wumpus/pitch 정보가 False로 기록된 경우를 추가로 고려.

        self.wumpus_candidates -= w_safe_to_remove
        self.pitch_candidates -= p_safe_to_remove
    
    def _get_adjacent_positions(self, x, y):
        return [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]

    def reset_for_respawn(self):
        self.x = 1 
        self.y = 1 
        self.direction = config.INITIAL_DIRECTION
        self.arrows = config.INITIAL_ARROWS
        self.has_gold = False
        self.just_bumped = False 
        self.last_bumped_direction = None
        if (self.x, self.y) in self.agent_knowledge:
            self.agent_knowledge[(self.x, self.y)]['bump'] = False
        else:
            self.agent_knowledge[(self.x, self.y)] = {
                'stench': None, 'breeze': None, 'glitter': None, 'wall': False,
                'wumpus': False, 'pitch': False, 'bump': False
            }

    def _get_action_to_reach(self, from_pos, to_pos):
        """from_pos에서 인접한 to_pos로 가기 위한 액션 문자열 반환"""
        fx, fy = from_pos
        tx, ty = to_pos
        if tx == fx + 1 and ty == fy: return 'MOVE_RIGHT'
        if tx == fx - 1 and ty == fy: return 'MOVE_LEFT'
        if ty == fy + 1 and tx == fx: return 'MOVE_UP'
        if ty == fy - 1 and tx == fx: return 'MOVE_DOWN'
        return None # 실제로는 인접해야만 호출됨

    def _find_shortest_known_path(self, target_x, target_y):
        """BFS를 사용하여 (self.x, self.y)에서 (target_x, target_y)까지 
           방문했고 안전한 칸으로만 이루어진 최단 경로의 첫 이동 액션을 찾습니다."""
        start_pos = (self.x, self.y)
        target_pos = (target_x, target_y)

        if start_pos == target_pos:
            return None # 이미 목표 위치에 있음 (또는 CLIMB을 위한 제자리 액션)

        queue = collections.deque([(start_pos, [])]) # (현재 위치, 현재까지의 액션 경로)
        # visited_bfs는 BFS 탐색 중에 방문한 노드를 추적하여 루프를 방지하고, 
        # 이미 최단 경로가 발견된 노드의 재탐색을 막습니다.
        # self.visited (에이전트가 게임 중 방문한 모든 셀)와는 다른 목적입니다.
        visited_bfs_path = {start_pos: []} # key: position, value: list of actions to reach it

        while queue:
            current_cell, path_to_current_cell = queue.popleft()

            if current_cell == target_pos:
                # 경로를 찾았으면, 시작점에서 첫 번째 액션 반환
                return path_to_current_cell[0] if path_to_current_cell else None

            for direction_action, game_dir_str in [('MOVE_RIGHT', 'RIGHT'), ('MOVE_LEFT', 'LEFT'), ('MOVE_UP', 'UP'), ('MOVE_DOWN', 'DOWN')]:
                next_x, next_y = current_cell
                if game_dir_str == 'UP': next_y += 1
                elif game_dir_str == 'DOWN': next_y -= 1
                elif game_dir_str == 'LEFT': next_x -= 1
                elif game_dir_str == 'RIGHT': next_x += 1
                
                next_cell = (next_x, next_y)

                # 다음 셀 조건: 
                # 1. 맵 범위 내
                # 2. 방문한 적 있는 셀 (self.visited)
                # 3. 에이전트 지식 상 안전한 셀 (_is_valid_and_known_safe)
                # 4. 이 BFS 탐색에서 아직 경로가 확정되지 않은 셀 (next_cell not in visited_bfs_path)
                if (1 <= next_x <= self.map_size[0] and 1 <= next_y <= self.map_size[1] and
                    next_cell in self.visited and 
                    self._is_valid_and_known_safe(next_x, next_y) and
                    next_cell not in visited_bfs_path):
                    
                    new_path = path_to_current_cell + [direction_action]
                    visited_bfs_path[next_cell] = new_path
                    queue.append((next_cell, new_path))
        
        return None # 경로를 찾지 못함

    def _find_shortest_path_to_target_matching_predicate(self, target_predicate, path_step_eval_func,
                                                        avoid_first_step_direction_if_bumped=None, 
                                                        exclude_first_step_to_pos=None):
        """BFS를 사용하여 현재 위치에서 target_predicate를 만족하고, 
           path_step_eval_func를 만족하는 경로로 이루어진 가장 가까운 셀까지의 첫 번째 이동 액션을 찾습니다."""
        start_pos = (self.x, self.y)
        
        queue = collections.deque([(start_pos, [])]) 
        visited_bfs = {start_pos} 

        while queue:
            current_cell, path_to_current_cell = queue.popleft()

            if current_cell != start_pos and target_predicate(current_cell):
                return path_to_current_cell[0] if path_to_current_cell else None

            action_directions_map = {
                'MOVE_UP': 'UP', 'MOVE_DOWN': 'DOWN', 
                'MOVE_LEFT': 'LEFT', 'MOVE_RIGHT': 'RIGHT'
            }
            sorted_actions = list(action_directions_map.keys()) 
            # random.shuffle(sorted_actions) # 필요시 탐색 순서 무작위화
            
            for action_str in sorted_actions:
                game_dir_str = action_directions_map[action_str]
                
                if not path_to_current_cell: 
                    if avoid_first_step_direction_if_bumped and game_dir_str == avoid_first_step_direction_if_bumped:
                        continue
                
                next_x, next_y = current_cell
                if game_dir_str == 'UP': next_y += 1
                elif game_dir_str == 'DOWN': next_y -= 1
                elif game_dir_str == 'LEFT': next_x -= 1
                elif game_dir_str == 'RIGHT': next_x += 1
                next_cell = (next_x, next_y)

                if not path_to_current_cell: 
                    if exclude_first_step_to_pos and next_cell == exclude_first_step_to_pos:
                        continue
                
                if path_step_eval_func(next_cell) and next_cell not in visited_bfs:
                    new_path = path_to_current_cell + [action_str]
                    visited_bfs.add(next_cell)
                    queue.append((next_cell, new_path))
        
        return None 

    def _is_strictly_safe_for_path(self, pos_tuple):
        """경로상 셀이 명확히 안전한지 (wumpus, pit False) 확인 (벽, 맵 범위 포함)"""
        return self._is_valid_and_known_safe(pos_tuple[0], pos_tuple[1])

    def _is_adventure_safe_for_path(self, pos_tuple):
        """경로상 셀이 모험 가능한 수준으로 안전한지 (wumpus, pit 확정 안됨) 확인"""
        x, y = pos_tuple
        if not (1 <= x <= self.map_size[0] and 1 <= y <= self.map_size[1]):
            return False
        if pos_tuple in self.discovered_walls:
            return False
        
        knowledge = self.agent_knowledge.get(pos_tuple, {})
        # Wumpus나 Pit으로 확정되지 않은 곳 (None이거나 False인 경우)
        return knowledge.get('wumpus') is not True and knowledge.get('pitch') is not True

    def choose_action(self):
        current_pos = (self.x, self.y)
        current_knowledge = self.agent_knowledge.get(current_pos, {})
        first_step_avoid_dir = self.last_bumped_direction if self.just_bumped else None
        
        # 1. 탈출 (Climb)
        if self.x == 1 and self.y == 1 and self.has_gold:
            return 'CLIMB'

        # 2. 금을 가지고 (1,1)로 복귀 (BFS를 통한 최단 경로 사용)
        if self.has_gold and current_pos != (1,1):
            next_action_to_home = self._find_shortest_known_path(1, 1) 
            if next_action_to_home:
                return next_action_to_home
            else:
                pass 

        # 3. 금 획득 (Grab Gold)
        if current_knowledge.get('glitter', False):
            return 'GRAB'

        # 4. 안전한 미방문 칸으로 이동 (금을 안 가진 경우)
        if not self.has_gold:
            current_previous_pos_for_P4_1 = self.previous_pos 
            
            # P4.1: 인접한 칸에 안전한 미방문 칸이 있으면 방문
            safe_adjacent_unvisited_moves = self._get_safe_unvisited_adjacent_moves(
                avoid_direction_if_bumped=first_step_avoid_dir,
                exclude_pos=current_previous_pos_for_P4_1
            )
            if safe_adjacent_unvisited_moves:
                chosen_move = random.choice(list(safe_adjacent_unvisited_moves.keys()))
                return chosen_move
            else:
                pass

            # P4.2.a: 인접 칸에 없으면, 떨어진 곳에 있는 '확실히 안전한 미방문 칸'을 '확실히 안전한 경로'로 방문 시도
            target_predicate_safe_unvisited = lambda p_tuple: \
                p_tuple not in self.visited and \
                self._is_valid_and_known_safe(p_tuple[0], p_tuple[1])

            action_to_safe_unvisited_strict_path = self._find_shortest_path_to_target_matching_predicate(
                target_predicate_safe_unvisited,
                self._is_strictly_safe_for_path, 
                avoid_first_step_direction_if_bumped=first_step_avoid_dir,
                exclude_first_step_to_pos=None 
            )
            if action_to_safe_unvisited_strict_path:
                return action_to_safe_unvisited_strict_path
            else:
                pass

        # 5. Wumpus 사냥 (금을 안 가진 경우, 화살 있을 때)
        if not self.has_gold and self.arrows > 0: 
            
            targets_to_hunt = list(self.confirmed_wumpuses) + \
                              list(self.wumpus_candidates - self.confirmed_wumpuses)
            
            if targets_to_hunt:
                # 5.1: 현재 위치에서 즉시 사격 가능한지 확인
                best_shot_target, best_shot_dir = None, None
                for w_pos in targets_to_hunt:
                    req_dir = self._get_direction_to_target(w_pos)
                    if req_dir and self._is_clear_shot_to(w_pos, req_dir):
                        best_shot_target = w_pos
                        best_shot_dir = req_dir
                        break # 첫 번째 유효한 목표 발견

                if best_shot_target:
                    if self.direction == best_shot_dir:
                        return 'SHOOT'
                    else: # 방향 전환
                        current_idx = self.direction_order.index(self.direction)
                        target_idx = self.direction_order.index(best_shot_dir)
                        diff = (target_idx - current_idx + 4) % 4
                        if diff == 1: return 'TURN_RIGHT'
                        elif diff == 3: return 'TURN_LEFT'
                        else: return 'TURN_RIGHT'
                
                # 5.2: 현재 위치에서 사격 불가 -> 사격 위치로 이동 계획
                def is_good_shooting_spot(p_tuple):
                    if not self._is_valid_and_known_safe(p_tuple[0], p_tuple[1]):
                        return False
                    for w_pos in targets_to_hunt:
                        req_dir = self._get_direction_to_target(w_pos, from_pos=p_tuple)
                        if req_dir and self._is_clear_shot_to(w_pos, req_dir, from_pos=p_tuple):
                            return True # 이 위치에서 쏠 수 있는 Wumpus가 하나라도 있음
                    return False
                
                # 가장 가까운 사격 지점으로 가는 첫 행동 찾기
                action_to_shooting_spot = self._find_shortest_path_to_target_matching_predicate(
                    is_good_shooting_spot,
                    self._is_strictly_safe_for_path, # 경로는 안전한 곳으로만
                    avoid_first_step_direction_if_bumped=first_step_avoid_dir,
                    exclude_first_step_to_pos=self.previous_pos
                )
                
                if action_to_shooting_spot:
                    return action_to_shooting_spot
            
        # 6. 모험 (Adventure) - 인접한 덜 위험한 미방문 칸 (금을 안 가진 경우) - Wumpus 사냥도 실패 시
        if not self.has_gold: 
            
            avoid_dir_for_adventure = self.last_bumped_direction if self.just_bumped else None 
            adventure_moves = self._get_adventure_moves(
                avoid_direction_if_bumped=avoid_dir_for_adventure, 
                exclude_pos=self.previous_pos
            )
            if adventure_moves:
                chosen_adventure_move = random.choice(list(adventure_moves.keys()))
                return chosen_adventure_move
            else:
                pass
                                
        # 7. 최후의 수단
        safe_fallback_moves = self._get_all_safe_adjacent_moves(
            avoid_direction_if_bumped=first_step_avoid_dir, 
            exclude_pos=self.previous_pos
        )
        action_current_dir = f'MOVE_{self.direction}'
        if action_current_dir in safe_fallback_moves:
            return action_current_dir
        other_safe_fallback_actions = [action for action in safe_fallback_moves if action != action_current_dir]
        if other_safe_fallback_actions:
            chosen_fallback_move = random.choice(other_safe_fallback_actions)
            return chosen_fallback_move
        final_fallback_directions = []
        for d_str in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            if d_str == first_step_avoid_dir: continue
            next_fx, next_fy = self._get_next_pos_for_direction(d_str)
            if (next_fx, next_fy) == self.previous_pos: continue
            if (next_fx, next_fy) in self.discovered_walls: continue
            if not (1 <= next_fx <= self.map_size[0] and 1 <= next_fy <= self.map_size[1]): continue
            final_fallback_directions.append(f'MOVE_{d_str}')
        if final_fallback_directions:
            chosen_final_move = random.choice(final_fallback_directions)
            return chosen_final_move
        return f'MOVE_{self.direction}'

    def _is_valid_and_known_safe(self, x, y):
        """주어진 좌표가 맵 범위 내에 있고, 벽이 아니며, Wumpus/Pit으로부터 안전한지 확인"""
        if not (1 <= x <= self.map_size[0] and 1 <= y <= self.map_size[1]):
            return False 
        if (x,y) in self.discovered_walls:
            return False

        pos_knowledge = self.agent_knowledge.get((x, y), {})
        # 확실히 Wumpus나 Pit이 있다고 알려진 경우
        if pos_knowledge.get('wumpus') is True or pos_knowledge.get('pitch') is True:
            return False 
        # 확실히 Wumpus와 Pit이 없다고 알려진 경우
        if pos_knowledge.get('wumpus') is False and pos_knowledge.get('pitch') is False:
            return True 
        
        # 확정된 위험 목록에 있는 경우 (위와 중복될 수 있으나 안전장치)
        if (x,y) in self.confirmed_wumpuses or (x,y) in self.confirmed_pitches:
            return False
            
        # 위 조건에 모두 해당하지 않으면, 해당 칸은 아직 wumpus나 pit 유무가 불확실 (None).
        # "known_safe"는 아니므로 False 반환. 모험 로직은 별도 처리.
        return False 

    def _get_next_pos_for_direction(self, direction):
        """(self.x, self.y) 에서 주어진 direction으로 한 칸 이동했을 때의 좌표를 반환합니다."""
        next_x, next_y = self.x, self.y
        if direction == 'UP': next_y += 1
        elif direction == 'DOWN': next_y -= 1
        elif direction == 'LEFT': next_x -= 1
        elif direction == 'RIGHT': next_x += 1
        return (next_x, next_y)

    def _get_safe_unvisited_adjacent_moves(self, avoid_direction_if_bumped=None, exclude_pos=None):
        safe_moves = {}
        action_directions_map = {'MOVE_UP': 'UP', 'MOVE_DOWN': 'DOWN', 'MOVE_LEFT': 'LEFT', 'MOVE_RIGHT': 'RIGHT'}
        for action, game_dir in action_directions_map.items():
            if avoid_direction_if_bumped and game_dir == avoid_direction_if_bumped:
                continue
            ax, ay = self._get_next_pos_for_direction(game_dir)
            if exclude_pos and (ax,ay) == exclude_pos:
                continue
            
            # 맵 범위, 벽, 방문 여부 체크는 _is_valid_and_known_safe에서 처리하지 않으므로 여기서 먼저 수행
            if not (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1]): continue 
            if (ax, ay) in self.discovered_walls: continue
            if (ax, ay) in self.visited: continue

            # _is_valid_and_known_safe는 wumpus/pitch가 False로 명시된 경우만 True를 반환
            if self._is_valid_and_known_safe(ax, ay):
                safe_moves[action] = (ax, ay)
        return safe_moves

    def _get_direction_to_target(self, target_pos, from_pos=None):
        tx, ty = target_pos
        cx, cy = from_pos if from_pos else (self.x, self.y)
        if tx == cx: 
            if ty > cy: return 'UP'
            if ty < cy: return 'DOWN'
        elif ty == cy: 
            if tx > cx: return 'RIGHT'
            if tx < cx: return 'LEFT'
        return None 

    def _is_clear_shot_to(self, target_pos, shot_direction, from_pos=None):
        """주어진 shot_direction으로 target_pos까지 화살을 쏠 때 방해물(다른 확정된 Wumpus/Pit, 벽)이 없는지 확인"""
        if not shot_direction: return False 
        
        path_to_target_inclusive = self._get_arrow_path(shot_direction, from_pos=from_pos) # 이 경로는 벽을 이미 고려함
        
        if target_pos not in path_to_target_inclusive: # shot_direction으로 target_pos에 도달할 수 없는 경우
            # (예: target_pos가 벽 뒤에 있거나, 방향이 완전히 틀린 경우)
            return False

        # target_pos 직전까지의 경로 (path_intermediate) 확인
        try:
            target_index = path_to_target_inclusive.index(target_pos)
            path_intermediate = path_to_target_inclusive[:target_index]
        except ValueError: # target_pos가 경로에 없는 경우 (이론상 위에서 걸러져야 함)
            return False

        for pos in path_intermediate:
            # discovered_walls는 _get_arrow_path에서 이미 체크됨
            # 해당 칸에 다른 확정된 위험 요소가 있는지 확인
            if pos in self.confirmed_wumpuses or pos in self.confirmed_pitches:
                return False
        return True

    def _get_adventure_moves(self, avoid_direction_if_bumped=None, exclude_pos=None):
        #'모험'을 할 수 있는 (덜 위험한 미방문, 벽 아닌) 인접 칸으로의 이동을 반환.
        adventure_moves = {}
        action_directions_map = {'MOVE_UP': 'UP', 'MOVE_DOWN': 'DOWN', 'MOVE_LEFT': 'LEFT', 'MOVE_RIGHT': 'RIGHT'}
        for action, game_dir in action_directions_map.items():
            if avoid_direction_if_bumped and game_dir == avoid_direction_if_bumped:
                continue
            ax, ay = self._get_next_pos_for_direction(game_dir)
            if exclude_pos and (ax,ay) == exclude_pos:
                continue
            if not (1 <= ax <= self.map_size[0] and 1 <= ay <= self.map_size[1]): continue
            if (ax,ay) in self.discovered_walls: continue
            if (ax, ay) in self.visited: continue # 모험은 미방문 칸 대상
            knowledge = self.agent_knowledge.get((ax, ay), {})
            # Wumpus나 Pit으로 확정되지 않은 곳 (None이거나 False인 경우)
            if knowledge.get('wumpus') is not True and knowledge.get('pitch') is not True:
                adventure_moves[action] = (ax,ay)
        return adventure_moves

    def _get_all_safe_adjacent_moves(self, avoid_direction_if_bumped=None, exclude_pos=None):
        #인접한 칸 중 (방문 여부 무관) 벽이 아니고 확실히 안전한(wumpus, pit False) 모든 이동 반환
        safe_moves = {}
        action_directions_map = {'MOVE_UP': 'UP', 'MOVE_DOWN': 'DOWN', 'MOVE_LEFT': 'LEFT', 'MOVE_RIGHT': 'RIGHT'}
        
        for action, game_dir in action_directions_map.items():
            if avoid_direction_if_bumped and game_dir == avoid_direction_if_bumped:
                continue
            
            ax, ay = self._get_next_pos_for_direction(game_dir)
            if exclude_pos and (ax,ay) == exclude_pos:
                continue
            
            if self._is_valid_and_known_safe(ax,ay): # wumpus, pit False이고 벽 아님
                safe_moves[action] = (ax,ay)
        return safe_moves