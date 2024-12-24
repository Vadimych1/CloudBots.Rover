from miniros.builtin_datatypes import Image
from PIL import Image as pilimg
import cv2

# Create image packet
image = Image()

# Load image
# Image is being converted to base64 string
image.load_image(pilimg.open("examples/test_image.jfif"))


# On the other side:
pil_im = image.get_image() # Get image as PIL.Image.Image
cv_im = image.get_image_array() # Get image as numpy.ndarray (can be used with OpenCV)

cv2.imshow("Image", cv_im)
cv2.waitKey(0)