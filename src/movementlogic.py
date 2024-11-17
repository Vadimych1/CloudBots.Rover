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
        return [speed, -speed, speed, -speed]
    
    def right(self, speed: float):
        return [-speed, speed, -speed, speed]
    
    def forward(self, speed: float):
        return [speed, speed, speed, speed]
    
    def backward(self, speed: float):
        return [-speed, -speed, -speed, -speed]

    def rotate_left(self, speed: float):
        return [-speed, -speed, speed, speed]
    
    def rotate_right(self, speed: float):
        return [speed, speed, -speed, -speed]
    
    def stop(self, speed: float):
        return [0, 0, 0, 0]