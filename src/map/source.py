import numpy as np
import math
import os
from collections import deque
from io import BytesIO
from PIL import Image, ImageDraw
import base64
import logging
import cv2
import time
import heapq

class Map:
    def __init__(self, path = "./chunks"):
        self.logger = logging.getLogger(f"Map[{path}]")
        self.chunks = self._reinit_chunks()
        self.path = path
    
    def _reinit_chunks(self):
        return {
            (cx, cy): Chunk(cx, cy) for cx in range(-2, 2) for cy in range(-2, 2)
        }
        # return {}
    
    def add_point(self, x, y):
        x /= 2
        y /= 2
        
        x = int(x)
        y = int(y)
        
        chunk_x = int(x // 1000)
        chunk_y = int(y // 1000)
        
        if (chunk_x, chunk_y) not in self.chunks:
            self.logger.info(f"Creating chunk at {chunk_x} {chunk_y}")
            self.chunks[(chunk_x, chunk_y)] = Chunk.load(chunk_x, chunk_y, self.path)
            # print(self.chunks[(chunk_x, chunk_y)])
            # print(self.chunks[(chunk_x, chunk_y)].data)

        self.chunks[(chunk_x, chunk_y)].data[int(x % 1000)][int(y % 1000)] = 255
    
    def create_path(self, x1, y1, x2, y2):
        self.logger.info(f"Finding path from {x1, y1} to {x2, y2}")
        
        path = self._find_path(x1, y1, x2, y2)
        
        self.logger.info(f"Path found! Processing {len(path) if path else 0} nodes")
        
        lines = []
        current_line = []
        
        if path is None:
            return None

        prev = path[0]
        p_dx, p_dy = None, None
        for x in path[1:]:
            dx, dy = x[0] - prev[0], x[1] - prev[1]
            if not (p_dx and p_dy):
                p_dx = dx
                p_dy = dy
            
            if p_dx == dx and p_dy == dy:
                current_line.append(x)
            else:
                lines.append((current_line[0], current_line[-1]))
                current_line = []
                p_dx, p_dy = None, None
            
            prev = x

        lines.append((current_line[0], current_line[-1]))
        
        
        return lines
    
    def _find_path(self, x1, y1, x2, y2):
        start_chunk_x = x1 // 1000
        start_chunk_y = y1 // 1000
        end_chunk_x = x2 // 1000
        end_chunk_y = y2 // 1000
        
        w = abs(start_chunk_x - end_chunk_x + 1)
        h = abs(start_chunk_y - end_chunk_y + 1)
        start_x = min(start_chunk_x, end_chunk_x)
        start_y = min(start_chunk_y, end_chunk_y)
        
        self._load_path_chunks((start_chunk_x, start_chunk_y), (end_chunk_x, end_chunk_y))
        
        constructed_map = np.zeros((int(1000 * w), int(1000 * h)))        
        
        for x in range(int(w)):
            for y in range(int(h)):
                d = (x + start_x, y + start_y)
                constructed_map[1000 * x:1000 * (x + 1), 1000 * y:1000 * (y + 1)] = self.chunks[d].data
                
        coord_x = min(x1, x2)
        coord_y = min(y1, y2)
        
        x_offs = 0
        y_offs = 0
        
        if coord_x < 0:
            x_offs = abs(coord_x) // 1000 * (coord_x / abs(coord_x)) * 1000
            x_offs -= 1000 if coord_x - x_offs < 0 else 0
        
        if coord_y < 0:
            y_offs = abs(coord_y) // 1000 * (coord_y / abs(coord_y)) * 1000
            y_offs -= 1000 if coord_y - y_offs < 0 else 0
        
        
        self.logger.info(f"Constructed map. Size: {constructed_map.shape}. Using BFS... {x1, x2, y1, y2, x_offs, y_offs}")
        
        self.path_offset = (x_offs, y_offs) 
        
        # return self._bfs(constructed_map, (x1 - x_offs, y1 - y_offs), (x2 - x_offs, y2 - y_offs))
        return self._astar(constructed_map, (x1 - x_offs, y1 - y_offs), (x2 - x_offs, y2 - y_offs))
    
                
    
    # PATHFINDING ALGOS
    def _bfs(self, data, start, end):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        
        start = tuple(map(int, start))
        end = tuple(map(int, end))
        
        self.logger.info(f"Running BFS. Start/end: {start}/{end}")
        
        queue = deque([start])
        visited = set()
        visited.add(start)
        parent = {start: None}

        i = 0
        while queue:
            if i % 10000 == 0:
                self.logger.info(f"Finding path. Iter {i}")
                
            current = queue.popleft()
            if current == end:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = parent[current]
                    
                self.logger.info(f"Finding path done in {i} iterations.")
                return path[::-1]  # Reverse path

            for direction in directions:
                neighbor = (current[0] + direction[0], current[1] + direction[1])
                
                if (0 <= neighbor[0] < data.shape[0] and
                    0 <= neighbor[1] < data.shape[1] and
                    neighbor not in visited and
                    data[neighbor] == 0):  # Assuming 0 is passable
                
                    queue.append(neighbor)
                    visited.add(neighbor)
                    parent[neighbor] = current
                    
            i += 1
            
        self.logger.info(f"Finding path done in {i} iterations.")

        return None  # Return None if no path is found

    def _astar(self, data, start, end):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        
        start = tuple(map(int, start))
        end = tuple(map(int, end))
        
        self.logger.info(f"Running A*. Start/end: {start}/{end}")
        
        rows, cols = data.shape

        open_set = []
        heapq.heappush(open_set, (0, start))  # Сохраняем кортеж (приоритет, координаты)
        
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._astar_heuristic(start, end)}

        i = 0
        while open_set:
            if i % 10000 == 0:
                self.logger.info(f"Finding path. Iter {i}")
            
            if i // 10000 >= 20:
                break
                
            current = heapq.heappop(open_set)[1]

            if current == end:
                # Воссоздание пути
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                
                self.logger.info(f"Finding path done in {i} iterations.")
                return path[::-1]  # Возвращаем путь в правильном порядке

            for direction in directions:
                neighbor = (current[0] + direction[0], current[1] + direction[1])

                # Проверяем границы карты и проходимость
                if (0 <= neighbor[0] < rows) and (0 <= neighbor[1] < cols) and (data[neighbor] == 0):
                    tentative_g_score = g_score[current] + 1  # Предполагаемое расстояние до соседа

                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        # Этот путь лучше, чем любой, который мы рассматривали
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self._astar_heuristic(neighbor, end)

                        if neighbor not in [i[1] for i in open_set]:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
                            
            i += 1
            
        self.logger.info(f"Finding path done in {i} iterations.")

        return None
        
    @staticmethod
    def _astar_heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    def _load_path_chunks(self, start_chunk, end_chunk):
        chunks_to_load = {start_chunk, end_chunk}
        dx = end_chunk[0] - start_chunk[0]
        dy = end_chunk[1] - start_chunk[1]
        length = int(math.sqrt(dx**2 + dy**2))
        if length > 0:
            for i in range(length + 1):
                x = start_chunk[0] + round(dx * i / length)
                y = start_chunk[1] + round(dy * i / length)
                chunks_to_load.add((x, y))
            
        for c in chunks_to_load:
            self.chunks[c] = Chunk.load(*c, self.path)
            
            
    def render(self, rx, ry, path, tx, ty):
        while "chunks" not in self.__dict__.keys():
            time.sleep(0.01)
            self.logger.info("Waiting for chunks")
            
        max_chunk_x = max(map(lambda x: x[0], self.chunks.keys()))
        max_chunk_y = max(map(lambda x: x[1], self.chunks.keys()))
        
        min_chunk_x = min(map(lambda x: x[0], self.chunks.keys()))
        min_chunk_y = min(map(lambda x: x[1], self.chunks.keys()))
        
        self.min_chunk_x = min_chunk_x
        self.min_chunk_y = min_chunk_y
        
        w, h = max_chunk_x - min_chunk_x, max_chunk_y - min_chunk_y
                
        per_chunk_x = 300
        per_chunk_y = 300
        
        img = Image.new('RGB', (int(per_chunk_x * w), int(per_chunk_y * h)), color='black')
        
        for (x, y), chunk in self.chunks.copy().items():
            data = Image.fromarray(chunk.data)
            data = data.resize((per_chunk_x, per_chunk_y))
            img.paste(data, (
                int(per_chunk_x * (x - min_chunk_x)), 
                int(per_chunk_y * (y - min_chunk_y)), 
                int(per_chunk_x * (x - min_chunk_x + 1)), 
                int(per_chunk_y * (y - min_chunk_y + 1))
            ))

        output = BytesIO()
        
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        
        draw = ImageDraw.ImageDraw(img)
        draw.circle(((rx / 1000 - min_chunk_x) * per_chunk_x, (ry / 1000 - min_chunk_y) * per_chunk_y), 20, "red", "green")
        
        if tx and ty:
            draw.circle(((tx / 1000 - min_chunk_x) * per_chunk_x, (ty / 1000 - min_chunk_y) * per_chunk_y), 10, "green", "red")
        
        if path:
            offs_x, offs_y = self.path_offset
            for line in path:
                draw.line(tuple(map(lambda l: ((l[0] + offs_x)/1000*per_chunk_x - min_chunk_x * per_chunk_x, (l[1] + offs_y)/1000*per_chunk_y - min_chunk_y * per_chunk_y), line)), "blue", 5)
                
        img.save(output, format="PNG")
        img.save("./lastmap.png", format="PNG")
        
        return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode('ascii')
    
    def haf_update_chunks(self):
        for chunk in self.chunks.values():
            chunk.update_by_haf()
    
    def __del__(self):
        self.logger.info("Saving chunks")
        for chunk in self.chunks:
            chunk.save(self.path)
        
class Chunk:    
    def __init__(self, x, y, data = None):
        self.d_x = x
        self.d_y = y
        self.data = data if data else np.zeros((1000, 1000), np.uint8)
    
    def update_by_haf(self):
        lines = cv2.HoughLinesP(self.data, 1, np.pi / 130, 100, minLineLength=10, maxLineGap=40)
        if lines is None:
            return
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(self.data, (x1, y1), (x2, y2), 255, 1)
    
    def save(self, path = "./chunks"):
        open(os.path.join(path, f"{self.d_x}_{self.d_y}.chunk"), "wb").write(self.data.flatten().tobytes(order='C'))
        
    @staticmethod
    def load(d_x, d_y, path = "./chunks"):
        try:
            return Chunk(d_x, d_y, np.frombuffer(open(os.path.join(path, f"{d_x}_{d_y}.chunk"), "rb").read(), dtype=np.uint8).reshape(1000, 1000))
        except:
            return Chunk(d_x, d_y)
    

# m = Map()
# print(m.create_path(0, 0, 10, 10))