import cv2, numpy
from enum import Enum

class Line:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        self.mid_x = (x1 + x2) / 2
        self.mid_y = (y1 + y2) / 2

class ActionType(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2

def yellow_white_mask(image: cv2.Mat, set_upper_half_to_black: bool = True, part: float = 3 / 5) -> cv2.Mat:
    """
    Создает бинарную маску изображения оттенков белого и желтого
    """
    im = image.copy()

    hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)

    lower_yellow = numpy.array([15, 100, 100])
    upper_yellow = numpy.array([35, 255, 255])
    lower_white = numpy.array([0, 0, 200])
    upper_white = numpy.array([255, 55, 255])

    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    mask_white = cv2.inRange(hsv, lower_white, upper_white)

    mask = cv2.bitwise_or(mask_yellow, mask_white)

    result = cv2.bitwise_and(im, im, mask=mask)
    if set_upper_half_to_black:
        result[:int(result.shape[0] * part), :] = 0

    return result

def kanny_lines_detector(image: cv2.Mat) -> cv2.Mat:
    """
    Находит границы объектов на изображении.
    Рекомендуется использовать `yellow_white_mask` перед обработкой этой функцией
    """
    return cv2.Canny(image, 100, 200)

def haf_lines_detector(image: cv2.Mat) -> list[Line]:
    """
    Находит границы объектов на изображении.
    Рекомендуется использовать `kanny_lines_detector` перед обработкой этой функцией
    """
    lines = cv2.HoughLinesP(image, 1, numpy.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)
    
    
    pl = []
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                pl.append(Line(x1, y1, x2, y2))
    return pl

def visualise_lines(image: cv2.Mat, lines: list[Line]):
    im = image.copy()
    for line in lines:
        cv2.line(im, (line.x1, line.y1), (line.x2, line.y2), (0, 0, 255), 6)
    return im

def detect(image: cv2.Mat) -> list[Line]:
    return haf_lines_detector(kanny_lines_detector(yellow_white_mask(image)))

def process_lines(lines: list[Line], image_width: int) -> ActionType:
    has_left_line = False
    has_center_line = False
    has_right_line = False

    for line in lines:
        if image_width / 6 < line.mid_x and line.mid_x < image_width / 3:
            has_left_line = True
        elif line.mid_x > image_width * 2 / 3 and line.mid_x < image_width * 5 / 6:
            has_right_line = True
        else:
            has_center_line = True

    if has_center_line:
        return ActionType.RIGHT
    elif has_right_line and has_center_line:
        return ActionType.RIGHT
    elif has_left_line and has_center_line:
        return ActionType.LEFT
    else:
        return ActionType.NONE

im = cv2.imread("./test.jfif")

mask = yellow_white_mask(im)
kanny = kanny_lines_detector(mask)
haf = haf_lines_detector(kanny)

visual = visualise_lines(im, haf)

cv2.imwrite("mask.jpg", mask)
cv2.imwrite("kanny.jpg", kanny)
cv2.imwrite("haf.jpg", visual)

print(process_lines(haf, im.shape[1]))