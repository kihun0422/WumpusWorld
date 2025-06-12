import random
import config # config.py 임포트 (WUMPUS_PROBABILITY 사용 위함)

class WumpusWorld:
    """Wumpus World 환경을 관리하는 클래스"""
    
    def __init__(self):
        self.wumpus_positions = set()  # 여러 마리 가능
        self.pitch_positions = set()
        self.gold_pos = None
        self.initialize_world()
    
    def initialize_world(self):
        """월드 초기화: Wumpus, Pitch, Gold 배치 (겹침 방지, 각각 최대 2개)"""
        # (1,1), (1,2), (2,1) 제외한 모든 가능한 위치 리스트 생성
        possible_spawn_positions = []
        for x in range(1, config.BOARD_SIZE + 1):
            for y in range(1, config.BOARD_SIZE + 1):
                if not ((x == 1 and y == 1) or (x == 1 and y == 2) or (x == 2 and y == 1)):
                    possible_spawn_positions.append((x,y))
        
        random.shuffle(possible_spawn_positions) # 위치를 섞음

        # Wumpus 배치 (최대 2개)
        wumpus_count = 0
        temp_possible_wumpus_spawns = list(possible_spawn_positions) # 복사해서 사용
        random.shuffle(temp_possible_wumpus_spawns)

        for pos in temp_possible_wumpus_spawns:
            if wumpus_count >= 2: break
            if random.random() < config.WUMPUS_PROBABILITY:
                self.wumpus_positions.add(pos)
                wumpus_count += 1
        
        self.pitch_positions.clear() # 혹시 모를 이전 정보 클리어
        pitch_count = 0
        temp_possible_pitch_spawns = list(possible_spawn_positions)
        random.shuffle(temp_possible_pitch_spawns)
        for pos in temp_possible_pitch_spawns:
            if pitch_count >= 2: 
                break
            if pos not in self.wumpus_positions: # Wumpus가 없는 위치에만
                if random.random() < config.PITCH_PROBABILITY: 
                    self.pitch_positions.add(pos)
                    pitch_count += 1
        
        # Gold 배치 (Wumpus, Pitch가 없는 곳 중 랜덤)
        available_positions_for_gold = []
        for x in range(1, config.BOARD_SIZE + 1):
            for y in range(1, config.BOARD_SIZE + 1):
                if (x == 1 and y == 1):  # 시작점은 금 배치에서 제외 유지
                    continue
                if (x, y) not in self.wumpus_positions and (x, y) not in self.pitch_positions:
                    available_positions_for_gold.append((x, y))
        
        if available_positions_for_gold:
            self.gold_pos = random.choice(available_positions_for_gold)
    
    def get_sensor_info(self, x, y):
        """현재 위치에서 센서 정보 반환"""
        sensor_info = {
            'stench': False,
            'breeze': False,
            'glitter': False,
            'wumpus': None,
            'pitch': None
        }
        
        # Stench 체크 (Wumpus 인접)
        for wx, wy in self.wumpus_positions:
            if abs(x - wx) + abs(y - wy) == 1:  # 맨하탄 거리 1
                sensor_info['stench'] = True
                break
        
        # Breeze 체크 (Pitch 인접)
        for px, py in self.pitch_positions:
            if abs(x - px) + abs(y - py) == 1:  # 맨하탄 거리 1
                sensor_info['breeze'] = True
                break
        
        # Glitter 체크 (Gold 동일 위치)
        if self.gold_pos == (x, y):
            sensor_info['glitter'] = True
        
        # 현재 위치에 실제 Wumpus/Pitch가 있는지 설정
        if (x, y) in self.wumpus_positions:
            sensor_info['wumpus'] = True
        else:
            sensor_info['wumpus'] = False
            
        if (x, y) in self.pitch_positions:
            sensor_info['pitch'] = True  
        else:
            sensor_info['pitch'] = False
        
        return sensor_info
    
    def remove_wumpus(self, pos):
        """Wumpus 제거"""
        if pos in self.wumpus_positions:
            self.wumpus_positions.remove(pos)
            return True
        return False
    
    def collect_gold(self, pos):
        """금 수집"""
        if self.gold_pos == pos:
            self.gold_pos = None
            return True
        return False
    
    def reset_world(self):
        """월드 리셋 (새 게임 시작)"""
        self.wumpus_positions.clear()
        self.pitch_positions.clear()
        self.gold_pos = None
        self.initialize_world()