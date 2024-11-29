import cv2

def histogram_compare_images(img1: cv2.Mat, img2: cv2.Mat):
    """
    Compares images by histograms.<br/>
    :param img1: first image<br/>
    :param img2: second image

    Load images by cv2.imread.
    """
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])

    res = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return res

def color_histogram_compare_images(img1: cv2.Mat, img2: cv2.Mat):
    """
    Compares images by color histograms.<br/>
    :param img1: first image<br/>
    :param img2: second image

    Load images by cv2.imread.
    """
    hist1 = cv2.calcHist([img1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([img2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])

    res = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return res
