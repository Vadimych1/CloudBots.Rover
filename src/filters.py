class BaseFilter:
    """
    Base filter class.
    """
    def __init__(self, size: int):
        self.size = size

    def filter(self, data: list[float]) -> list[float]:
        return data
    
    def reset(self):
        pass

class MedianFilter(BaseFilter):
    """
    Filters values by taking the median of the 3 last values.
    @param size: Size of data array.
    """
    def __init__(self, size: int):
        self.size = size
        self.prev_data = None
        self.current_data = None
 
    def filter(self, data: list[float]) -> list[float]:   
        """
        Filters value provided by data.
        """
        if self.current_data is None:
            self.current_data = data
            return data
    
        if self.prev_data is None:
            self.prev_data = self.current_data
            self.current_data = data
            return data

        result = []
        for i in range(self.size):
            arr = [data[i], self.prev_data[i], self.current_data[i]]
            arr.sort()
            result.append(arr[1])

        self.prev_data = self.current_data
        self.current_data = data

        return result

    def reset(self):
        """
        Resets the filter.
        """
        self.prev_data = None
        self.current_data = None

class KalmanFilter(BaseFilter):
    """
    Filters values by using Kalman filter.<br>
    @param size: Size of data array.
    """
    def __init__(self, size: int):
        self.size = size
        self.data = [
            {
                "x": 0, # Initial estimate
                "P": 1, # Initial estimate error covariance
                "Q": 0.1, # Process noise covariance
                "R": 0.1, # Measurement noise covariance
                "A": 1, # State transition coefficient
                "B": 0, # Control input coefficient
                "H": 1, # Measurement function coefficient
                "K": 0 # Kalman gain
            } for _ in range(size)
        ]

    def _filter(self, data: float, index: str):
        self.data[index]["x"] = self.data[index]["A"] * self.data[index]["x"] + self.data[index]["B"] * data
        self.data[index]["P"] = self.data[index]["A"] * self.data[index]["P"] * self.data[index]["A"] + self.data[index]["Q"]
        self.data[index]["K"] = self.data[index]["P"] * self.data[index]["H"] / (self.data[index]["H"] * self.data[index]["P"] * self.data[index]["H"] + self.data[index]["R"])
        self.data[index]["x"] = self.data[index]["x"] + self.data[index]["K"] * (data - self.data[index]["H"] * self.data[index]["x"])
        self.data[index]["P"] = (1 - self.data[index]["K"] * self.data[index]["H"]) * self.data[index]["P"]
        return self.data[index]["x"]
       
    def filter(self, data: list[float]) -> list[float]:  
        """
        Filters value provided by data.
        """
        return [self._filter(data[i], i) for i in range(self.size)]

    def reset(self):
        """
        Resets the filter.
        """
        self.data = [
            {
                "x": 0,
                "P": 1,
                "Q": 0.1,
                "R": 0.1,
                "A": 1,
                "B": 0,
                "H": 1,
                "K": 0
            } for _ in range(self.size)
        ]