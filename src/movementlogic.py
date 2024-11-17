class BaseMovementLogic:
    def stop(self, speed: float):
        raise NotImplementedError

    def left(self, speed: float):
        raise NotImplementedError
    
    def right(self, speed: float):
        raise NotImplementedError
    
    def forward(self, speed: float):
        raise NotImplementedError
    
    def backward(self, speed: float):
        raise NotImplementedError

    def rotate_left(self, speed: float):
        raise NotImplementedError
    
    def rotate_right(self, speed: float):
        raise NotImplementedError

class RollingMovementLogic(BaseMovementLogic):
    def left(self, speed: float):
        return [speed, 0, -speed, 0]
    
    def right(self, speed: float):
        return [-speed, 0, speed, 0]
    
    def forward(self, speed: float):
        return [0, speed, 0, speed]
    
    def backward(self, speed: float):
        return [0, -speed, 0, -speed]

    def rotate_left(self, speed: float):
        return [speed, 0, 0, -speed]
    
    def rotate_right(self, speed: float):
        return [-speed, 0, 0, speed]
    
    def stop(self, speed: float):
        return [0, 0, 0, 0]