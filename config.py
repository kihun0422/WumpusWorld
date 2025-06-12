"""
게임 설정 및 상수 정의
"""

# 게임 보드 설정
BOARD_SIZE = 4  # 4x4 격자
START_POSITION = (1, 1)  # 시작 위치
INITIAL_DIRECTION = 'RIGHT'  # 초기 방향 (동쪽)

# 확률 설정
WUMPUS_PROBABILITY = 0.1  # Wumpus 생성 확률
PITCH_PROBABILITY = 0.1   # 웅덩이 생성 확률

# 에이전트 초기 상태
INITIAL_ARROWS = 3  # 초기 화살 개수

# UI 설정
WINDOW_WIDTH = 1040
WINDOW_HEIGHT = 620
CELL_SIZE = 80
WINDOW_TITLE = "Wumpus World - Agent Knowledge vs Real World"

# 색상 설정
COLORS = {
    'background': 'white',
    'wall': 'lightgray',
    'discovered_wall': 'brown',
    'visited_safe': 'white',
    'glitter_bg': '#ffffcc',    # 연한 금색
    'stench_bg': '#ffcccc',     # 연한 빨간색  
    'breeze_bg': '#ccddff',     # 연한 파란색
    'stench_breeze_bg': '#e6ccff',  # 연한 보라색
    'wumpus_confirmed': '#ffb3ba',  # 진한 연분홍
    'pitch_confirmed': '#bae1ff',   # 진한 연파랑
    'unknown': 'darkgray',
    'candidate': 'lightgray',
    'agent': 'red',
    'wumpus': 'purple',
    'pitch': 'blue',
    'gold': 'gold'
}

# 폰트 설정
FONTS = {
    'title': ('Arial', 14, 'bold'),
    'info': ('Arial', 12),
    'control': ('Arial', 10),
    'sensor': ('Arial', 11),
    'legend': ('Arial', 9),
    'cell_text': ('Arial', 9),
    'object': ('Arial', 20, 'bold'),
    'unknown': ('Arial', 16)
}

# 방향 설정
DIRECTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']
DIRECTION_VECTORS = {
    'UP': (0, 1),
    'DOWN': (0, -1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0)
}

# 키 매핑
KEY_MAPPING = {
    'Up': 'UP',
    'Down': 'DOWN', 
    'Left': 'LEFT',
    'Right': 'RIGHT',
    'g': 'grab',
    'G': 'grab',
    's': 'shoot',
    'S': 'shoot',
    'c': 'climb',
    'C': 'climb'
}

# 센서 타입
SENSOR_TYPES = {
    'stench': 'wumpus',
    'breeze': 'pitch',
    'glitter': 'gold',
    'bump': 'wall',
    'scream': 'wumpus_killed'
}

# 게임 오브젝트 타입
OBJECT_TYPES = {
    'wumpus': 'W',
    'pitch': 'P', 
    'gold': 'G'
}

# 메시지
MESSAGES = {
    'game_over': {
        'wumpus': "Wumpus와 마주침",
        'pitch': "웅덩이에 빠짐",
        'success': "금을 가지고 탈출"
    },
    'actions': {
        'wall_hit': "벽에 부딪혔습니다",
        'gold_collected': "금을 획득",
        'no_arrows': "화살이 없습니다!",
        'arrow_miss': "빗나갔습니다!",
        'wumpus_killed': "Scream! Wumpus가 제거되었습니다!",
        'climb_wrong_position': "(1,1) 위치에서만 탈출할 수 있습니다!",
        'climb_no_gold': "금을 가지고 있어야 탈출할 수 있습니다!"
    }
}

# 범례 텍스트
LEGEND_TEXTS = [
    "범례 - S: Stench, B: Breeze, G: Glitter",
    "W?: Wumpus 후보, P?: Pitch 후보",  
    "WUMPUS/PITCH: 확정된 위치",
    "배경색 - 금색: Glitter, 빨강: Stench, 파랑: Breeze, 보라: Stench+Breeze",
    "연분홍: Wumpus 확정, 연파랑: Pitch 확정, 갈색: 확인된 벽"
]

# 디버그 설정
DEBUG = {
    'enabled': True,
    'show_reasoning': True,
    'show_candidates': True,
    'show_confirmations': True
}