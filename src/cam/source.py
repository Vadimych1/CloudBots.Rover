import cv2 as cv
import threading
from typing import Callable
from cv2.typing import MatLike
import logging
import time
import numpy as np
from sklearn.cluster import KMeans 
from collections import Counter
from enum import Enum
from itertools import groupby as g


class R_BaseCamHandler:
    """
    A handler class that can be passed to R_Cam.add_handler

    Does not stop the thread by just setting data to property instead of calling function
    
    Supports `threading`
    """
    def __init__(self):
        self.frame = None
        self.ready = False

    def __call__(self, frame: MatLike):
        if type(frame) == type(None):
            return
        
        self.frame = frame
        self.ready = True

    def get(self):
        """
        Returns current data frame
        """
        if self.ready:
            self.ready = False
            return self.frame

        return None

    def cget(self):
        """
        Returns a copy of current data frame 
        """
        r = self.get()

        if type(r) == type(None):
            return None
        else:
            return r.copy()
    
    def loop(self):
        """
        Your custom code here
        """


class R_Cam:
    """
    Camera module for robot
    """


    def __init__(self, stream_addr: int = 0):
        self.cam_n = stream_addr
        self.cap = cv.VideoCapture(stream_addr)
        self.handlers = []
        self.running = False
        self.logger = logging.getLogger(f"CAM[{stream_addr}]")
        self.thread = None


    def add_handler(self, handler: Callable[[MatLike], None] | R_BaseCamHandler):
        self.handlers.append(handler)


    def _frame(self, frame: MatLike):
        for h in self.handlers:
            try:
                h(frame)
            except Exception as e:
                self.logger.error("Exception while calling handler:")
                self.logger.exception(e)


    def run(self) -> threading.Thread:
        """
        Returns thread with mainloop
        """
        self.running = True
        self.thread = threading.Thread(target=self._thread)

        return self.thread


    def stop(self):
        """
        Stop the camera frame stream
        """
        self.running = False


    def _thread(self):
        while self.cap.isOpened() and self.running:
            ret, frame = self.cap.read()
            
            if ret:
                self._frame(frame)


class ObstacleSide(Enum):
    """
    Represents the alignment of detected obstacle
    """
    LEFT = 0
    RIGHT = 1
    CENTER = 2


class R_ObstacleDetectorHandler(R_BaseCamHandler):
    """
    Detects the visible obstacles on frames provided by camera stream
    """


    MIN_LENGTH = 40
    MAX_X_DELTA = 40
    MAX_BOTTOM_PADDING = 70


    def __init__(self):
        super().__init__()
        self.thread = None
        self.running = False
        self.results = []
        self.result = None


    def get_data(self):
        """
        Returns current state of detector
        """
        return self.result


    def run(self):
        """
        Returns thread with mainloop
        """
        self.running = True
        self.thread = threading.Thread(target=self.loop)
        return self.thread


    def loop(self):
        """
        Mainloop
        """
        while self.running:
            frame = self.cget()

            if type(frame) != type(None):
                self.results.append(self.process(frame))
                if len(self.results) > 7:
                    self.results = self.results[1:]
                self.result = Counter(self.results).most_common(1)[0][0]
            else:
                time.sleep(0.02)


    @staticmethod
    def get_dominant(im: MatLike) -> np.ndarray:
        """
        Returns the most used color of image

        :param im: input image
        :return: dominant color
        :rtype: ndarray
        """
        im = im.reshape((im.shape[0] * im.shape[1], 3))
        clt = KMeans(4)
        labels = clt.fit_predict(im)
        lcounts = Counter(labels)
        dominant = clt.cluster_centers_[lcounts.most_common(1)[0][0]]
        return dominant


    def process(self, f: MatLike, threshold: int = 25, alpha: int = 5, canny_A: int = 200, canny_B: int = 200, percent_height: float = 2/3) -> ObstacleSide:
        """
        Processes input image to detect obstacles

        Returns side of obstacle (left/right/center)
        
        :param f: image
        :param threshhold: threshhold of dominant color mask
        :param alpha: gaussian blur strengh
        :param canny_A: Canny filter first threshold
        :param canny_B: Canny filter second threshold
        :param percent_height: height of image used to detect objects (from bottom side)

        :return: `side` of obstacle or `None` if no obstacle was detected
        :rtype: ObstacleSide | None
        """

        f = f[int(f.shape[0]*(1-percent_height)):f.shape[0]] # process only percent_height of image (from bottom)
        dominant = R_ObstacleDetectorHandler.get_dominant(f) # get the dominant color of image (the mostly seen)
        masked = cv.inRange(f, dominant - threshold, dominant + threshold) # apply mask by dominant color
        blur = cv.GaussianBlur(masked, (alpha, alpha), 10, borderType=cv.BORDER_DEFAULT) # blur image to destroy artifacts
        canny = cv.Canny(blur, canny_A, canny_B) # get object borders by Canny

        # cv.imshow("blur", bls

        circles = cv.HoughCircles(canny, cv.HOUGH_GRADIENT, 1, f.shape[0] / 8, param1=100, param2=30, minRadius=30)
        lines = cv.HoughLinesP(canny, 1, np.pi/180, 80, None, 0, 10) # detect lines by Hough

        # get only vertical lines that start above `percent_height`
        result = []
        if type(lines) != type(None):
            # print("L", lines)
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if max(y1, y2) > f.shape[0] - self.MAX_BOTTOM_PADDING and abs(y1 - y2) > self.MIN_LENGTH and abs(x1 - x2) < self.MAX_X_DELTA:
                    result.append((x1 + x2) / 2)
        else:
            return None


        if type(circles) != type(None):
            # print("C", circles)
            for circle in circles:
                cx, cy, _ = circle[0]
                if cy > f.shape[0] - self.MAX_BOTTOM_PADDING:
                    result.append(cx)
        else:
            return None


        # select obstacle side
        if len(result) > 0:
            mid = sum(result) / len(result)

            if mid < f.shape[1] / 3:
                return ObstacleSide.LEFT
            elif mid < f.shape[1] / 3 * 2:
                return ObstacleSide.CENTER
            else:
                return ObstacleSide.LEFT
        else:
            return None


# d = R_ObstacleDetectorHandler()

# cap = cv.VideoCapture(0)
# while True:
#     ret, frame = cap.read()

#     result = d.process(frame)

#     print(result)

#     if cv.waitKey(1) == ord('q'):
#         break

# cap.release()