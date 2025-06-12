import tkinter as tk

class WumpusUI:
    """Wumpus World GUI 관리 클래스"""
    
    def __init__(self, agent, world):
        self.agent = agent
        self.world = world
        self.cell_size = 80
        
        self.root = tk.Tk()
        self.root.title("Wumpus World - Agent Knowledge vs Real World")
        self.canvas = tk.Canvas(self.root, width=1040, height=620, bg='white')
        self.canvas.pack()
    
    def draw_all(self):
        """전체 화면 그리기"""
        self.canvas.delete('all')
        
        # 왼쪽 격자 (에이전트 인지 정보)
        self.draw_agent_grid(0)
        
        # 오른쪽 격자 (실제 월드)
        self.draw_real_world_grid(520)
        
        # 구분선
        self.canvas.create_line(520, 0, 520, 480, fill='black', width=3)
        
        # 범례 및 정보 표시
        self.draw_info()
    
    def draw_agent_grid(self, offset_x):
        """에이전트가 인지한 정보 격자"""
        # 제목
        self.canvas.create_text(offset_x + 240, 20, text="Agent Knowledge", 
                               font=('Arial', 14, 'bold'))
        
        for i in range(6):
            for j in range(6):
                x = offset_x + i * self.cell_size
                y = 40 + (5 - j) * self.cell_size  # 좌표 변환
                
                # 벽 영역
                if i == 0 or i == 5 or j == 0 or j == 5:
                    wall_color = 'brown' if (i, j) in self.agent.discovered_walls else 'lightgray'
                    self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                               fill=wall_color, outline='black', width=2)
                
                # 게임 영역
                elif 1 <= i <= 4 and 1 <= j <= 4:
                    if (i, j) in self.agent.visited:
                        # 방문한 격자
                        bg_color = self._get_visited_cell_color(i, j)
                        self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                                   fill=bg_color, outline='black', width=2)
                        
                        # 센서 정보 표시
                        info_text = self._get_sensor_display_text(i, j)
                        if info_text:
                            self.canvas.create_text(x + self.cell_size//2, y + self.cell_size//2,
                                                  text=info_text, font=('Arial', 9))
                    else:
                        # 미방문 격자
                        self._draw_unvisited_cell(x, y, i, j)
                
                # 격자 선
                self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                           fill='', outline='black', width=1)
        
        # 에이전트 위치 (삼각형)
        self._draw_triangle(offset_x, self.agent.x, self.agent.y, self.agent.direction, 'red')
        
        # 하단 정보 표시
        self._draw_agent_status(240, 540)
    
    def draw_real_world_grid(self, offset_x):
        """실제 월드 상태 격자"""
        # 제목
        self.canvas.create_text(offset_x + 240, 20, text="Real World", 
                               font=('Arial', 14, 'bold'))
        
        for i in range(6):
            for j in range(6):
                x = offset_x + i * self.cell_size
                y = 40 + (5 - j) * self.cell_size  # 좌표 변환
                
                # 벽 영역
                if i == 0 or i == 5 or j == 0 or j == 5:
                    self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                               fill='gray', outline='black', width=2)
                # 게임 영역
                else:
                    self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                               fill='white', outline='black', width=2)
                    
                    # 객체 표시
                    if (i, j) in self.world.wumpus_positions:
                        self.canvas.create_text(x + self.cell_size//2, y + self.cell_size//2,
                                              text='W', font=('Arial', 20, 'bold'), fill='purple')
                    
                    if (i, j) in self.world.pitch_positions:
                        self.canvas.create_text(x + self.cell_size//2, y + self.cell_size//2,
                                              text='P', font=('Arial', 20, 'bold'), fill='blue')
                    
                    if (i, j) == self.world.gold_pos:
                        self.canvas.create_text(x + self.cell_size//2, y + self.cell_size//2,
                                              text='G', font=('Arial', 20, 'bold'), fill='gold')
        
        # 에이전트 위치 (삼각형)
        self._draw_triangle(offset_x, self.agent.x, self.agent.y, self.agent.direction, 'red')
    
    def _get_visited_cell_color(self, i, j):
        """방문한 셀의 배경색 결정"""
        # 확정된 위험 우선 표시
        if (i, j) in self.agent.confirmed_wumpuses:
            return '#ffb3ba'  # 진한 연분홍 (Wumpus 확정)
        if (i, j) in self.agent.confirmed_pitches:
            return '#bae1ff'  # 진한 연파랑 (Pitch 확정)

        bg_color = 'white'
        sensor_info = self.agent.agent_knowledge.get((i, j), {})
        
        # Glitter가 있으면 금색 배경
        if sensor_info.get('glitter', False):
            bg_color = '#ffffcc'  # 연한 금색
        # Stench가 있으면 연한 빨간색 배경
        elif sensor_info.get('stench', False):
            bg_color = '#ffcccc'  # 연한 빨간색
        # Breeze가 있으면 연한 파란색 배경
        elif sensor_info.get('breeze', False):
            bg_color = '#ccddff'  # 연한 파란색
        
        # Stench와 Breeze가 동시에 있으면 보라색 (Glitter 우선)
        if (sensor_info.get('stench', False) and sensor_info.get('breeze', False) 
            and not sensor_info.get('glitter', False)):
            bg_color = '#e6ccff'  # 연한 보라색
        
        return bg_color
    
    def _draw_unvisited_cell(self, x, y, i, j):
        """미방문 셀 그리기"""
        is_candidate = ((i, j) in self.agent.wumpus_candidates or 
                       (i, j) in self.agent.pitch_candidates or
                       (i, j) in self.agent.confirmed_wumpuses or 
                       (i, j) in self.agent.confirmed_pitches)
        
        if is_candidate:
            # 후보/확정 격자 - 배경색 결정
            bg_color = 'lightgray'
            
            # 확정된 위치는 더 진한 배경색
            if (i, j) in self.agent.confirmed_wumpuses:
                bg_color = '#ffb3ba'  # 진한 연분홍 (Wumpus 확정)
            elif (i, j) in self.agent.confirmed_pitches:
                bg_color = '#bae1ff'  # 진한 연파랑 (Pitch 확정)
            
            self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                       fill=bg_color, outline='black', width=2)
            
            # 후보/확정 정보 표시
            candidate_text = []
            if (i, j) in self.agent.wumpus_candidates and (i, j) not in self.agent.confirmed_wumpuses:
                candidate_text.append('W?')
            if (i, j) in self.agent.pitch_candidates and (i, j) not in self.agent.confirmed_pitches:
                candidate_text.append('P?')
            
            # 확정된 위치 표시
            if (i, j) in self.agent.confirmed_wumpuses:
                candidate_text.append('WUMPUS')
            if (i, j) in self.agent.confirmed_pitches:
                candidate_text.append('PITCH')
            
            if candidate_text:
                color = 'darkred' if any('WUMPUS' in text or 'PITCH' in text for text in candidate_text) else 'red'
                font_size = 8 if any('WUMPUS' in text or 'PITCH' in text for text in candidate_text) else 10
                self.canvas.create_text(x + self.cell_size//2, y + self.cell_size//2,
                                      text='\n'.join(candidate_text), font=('Arial', font_size), fill=color)
        else:
            # 완전 미방문 격자 - 어두운 색 + ?
            self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                       fill='darkgray', outline='black', width=2)
            self.canvas.create_text(x + self.cell_size//2, y + self.cell_size//2,
                                  text='?', font=('Arial', 16), fill='white')
    
    def _get_sensor_display_text(self, x, y):
        """센서 정보 표시 텍스트 생성"""
        if (x, y) not in self.agent.agent_knowledge:
            return ""
        
        info = self.agent.agent_knowledge[(x, y)]
        text_parts = []

        # 확정된 정보 우선 표시
        if (x,y) in self.agent.confirmed_wumpuses:
            text_parts.append('WUMPUS')
        elif (x,y) in self.agent.confirmed_pitches: # Wumpus와 Pitch가 동시에 있을 수 없다는 가정 하에 elif 사용
            text_parts.append('PITCH')
        else: # 확정된 위험이 아닐 경우에만 센서 및 후보 정보 표시
            if info.get('stench', False):
                text_parts.append('S')
            if info.get('breeze', False):
                text_parts.append('B')
            if info.get('glitter', False):
                text_parts.append('G')
            
            # 후보 정보 추가 (확정되지 않았을 때만 의미 있음)
            if (x, y) in self.agent.wumpus_candidates and (x,y) not in self.agent.confirmed_wumpuses:
                text_parts.append('W?')
            if (x, y) in self.agent.pitch_candidates and (x,y) not in self.agent.confirmed_pitches:
                text_parts.append('P?')
        
        return '\n'.join(text_parts)
    
    def _draw_triangle(self, offset_x, x, y, direction, color):
        """방향에 따른 삼각형 그리기"""
        center_x = offset_x + x * self.cell_size + self.cell_size // 2
        center_y = 40 + (5 - y) * self.cell_size + self.cell_size // 2
        size_x = 15  # 가로 크기
        size_y = 20  # 세로 크기

        if direction == 'RIGHT':
            points = [
                center_x + size_x, center_y,           # 오른쪽 꼭짓점
                center_x - size_x, center_y - size_y,  # 왼쪽 위
                center_x - size_x, center_y + size_y   # 왼쪽 아래
            ]
        elif direction == 'UP':
            points = [
                center_x, center_y - size_y,           # 위쪽 꼭짓점
                center_x - size_x, center_y + size_y,  # 왼쪽 아래
                center_x + size_x, center_y + size_y   # 오른쪽 아래
            ]
        elif direction == 'LEFT':
            points = [
                center_x - size_x, center_y,           # 왼쪽 꼭짓점
                center_x + size_x, center_y - size_y,  # 오른쪽 위
                center_x + size_x, center_y + size_y   # 오른쪽 아래
            ]
        elif direction == 'DOWN':
            points = [
                center_x, center_y + size_y,           # 아래쪽 꼭짓점
                center_x - size_x, center_y - size_y,  # 왼쪽 위
                center_x + size_x, center_y - size_y   # 오른쪽 위
            ]
        
        return self.canvas.create_polygon(points, fill=color, outline='black', width=2)
    
    def _draw_agent_status(self, x, y):
        """에이전트 상태 정보 표시"""
        info_text = f"위치: ({self.agent.x}, {self.agent.y}) | 방향: {self.agent.direction} | 화살: {self.agent.arrows}개 | 금: {'있음' if self.agent.has_gold else '없음'}"
        self.canvas.create_text(x, y, text=info_text, font=('Arial', 12))
        
        # 조작법 안내
        control_text = "조작: 방향키(이동) | G(금획득) | S(화살발사) | C(탈출)"
        self.canvas.create_text(x, y + 20, text=control_text, font=('Arial', 10), fill='gray')
        
        # 센서 상태 표시
        current_sensors = self.agent.agent_knowledge.get((self.agent.x, self.agent.y), {})
        sensor_status = []
        if current_sensors.get('stench', False):
            sensor_status.append('STENCH')
        if current_sensors.get('breeze', False):
            sensor_status.append('BREEZE')
        if current_sensors.get('glitter', False):
            sensor_status.append('GLITTER')
        if current_sensors.get('bump', False):
            sensor_status.append('BUMP')
            
        sensor_text = f"현재 센서: {', '.join(sensor_status) if sensor_status else '없음'}"
        self.canvas.create_text(x, y + 40, text=sensor_text, font=('Arial', 11), fill='blue')
    
    def draw_info(self):
        """범례 표시"""
        # 범례 (Real World 격자 아래)
        legend_y = 540
        legend_texts = [
            "범례 - S: Stench, B: Breeze, G: Glitter",
            "W?: Wumpus 후보, P?: Pitch 후보",  
            "WUMPUS/PITCH: 확정된 위치",
            "배경색 - 금색: Glitter, 빨강: Stench, 파랑: Breeze, 보라: Stench+Breeze",
            "연분홍: Wumpus 확정, 연파랑: Pitch 확정, 갈색: 확인된 벽"
        ]
        
        for i, text in enumerate(legend_texts):
            self.canvas.create_text(780, legend_y + i * 15, text=text, 
                                   font=('Arial', 9), fill='gray')
    
    def bind_keys(self, handler):
        """키 이벤트 바인딩"""
        self.root.bind('<Key>', handler)
        self.root.focus_set()
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()
    
    def quit(self):
        """GUI 종료"""
        self.root.quit()