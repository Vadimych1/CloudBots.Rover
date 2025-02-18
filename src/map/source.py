import numpy as np
import math
import os
from collections import deque
from io import BytesIO
from PIL import Image, ImageDraw
import base64
import logging

class Map:
    def __init__(self, path = "./chunks"):
        self.logger = logging.getLogger(f"Map[{path}]")
        self.chunks = {}
        self.path = path
        
    def add_point(self, x, y):
        chunk_x = int(x // 1000)
        chunk_y = int(y // 1000)
        
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk.load(chunk_x, chunk_y, self.path)
        self.chunks[(chunk_x, chunk_y)].data[int(x % 1000)][int(y % 1000)] = 255
    
    def create_path(self, x1, y1, x2, y2):
        self.logger.info(f"Finding path from {x1, y1} to {x2, y2}")
        
        path = self._find_path(x1, y1, x2, y2)
        
        lines = []
        current_line = []

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
        
        constructed_map = np.zeros((1000 * w, 1000 * h))        
        
        for x in range(w):
            for y in range(h):
                d = (x + start_x, y + start_y)
                constructed_map[1000 * x:1000 * (x + 1), 1000 * y:1000 * (y + 1)] = self.chunks[d].data
                
        return self._bfs(constructed_map, (x1, y1), (x2, y2))
                
        
    def _bfs(self, data, start, end):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]
        
        queue = deque([start])
        visited = set()
        visited.add(start)
        parent = {start: None}

        while queue:
            current = queue.popleft()
            if current == end:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = parent[current]
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

        return None  # Return None if no path is found

        
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
            
            
    def render(self, rx, ry):        
        max_chunk_x = max(map(lambda x: x[0], self.chunks.keys()))
        max_chunk_y = max(map(lambda x: x[1], self.chunks.keys()))
        
        min_chunk_x = min(map(lambda x: x[0], self.chunks.keys()))
        min_chunk_y = min(map(lambda x: x[1], self.chunks.keys()))
        
        w, h = max_chunk_x - min_chunk_x, max_chunk_y - min_chunk_y
                
        per_chunk_x = 300
        per_chunk_y = 300
        
        img = Image.new('RGB', (int(per_chunk_x * w), int(per_chunk_y * h)), color='black')
        
        
        for (x, y), chunk in self.chunks.copy().items():
            data = Image.fromarray(chunk.data)
            data = data.resize((per_chunk_x, per_chunk_y))
            img.paste(data, (
                per_chunk_x * (x - min_chunk_x), 
                per_chunk_y * (y - min_chunk_y), 
                per_chunk_x * (x - min_chunk_x + 1), 
                per_chunk_y * (y - min_chunk_y + 1)
            ))

        draw = ImageDraw.ImageDraw(img)
        draw.circle(((rx / 1000 - min_chunk_x) * per_chunk_x, (ry / 1000 - min_chunk_y) * per_chunk_y), 20, "red", "green")

        output = BytesIO()
        
        img.save(output, format="PNG")
        img.save("./lastmap.png", format="PNG")
        
        return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode('ascii')
    
    def __del__(self):
        self.logger.info("Saving chunks")
        for chunk in self.chunks:
            chunk.save(self.path)
        
class Chunk:    
    def __init__(self, x, y, data = None):
        self.d_x = x
        self.d_y = y
        self.data = data or np.zeros((1000, 1000), np.uint8)
        
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