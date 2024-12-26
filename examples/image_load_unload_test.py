from miniros.builtin_datatypes import Image
from PIL import Image as pilimg
import time
import numpy

start = time.time()
pack = Image()
im = pilimg.fromarray(numpy.random.randint(0, 255, (100, 100, 3), dtype=numpy.uint8)).convert("RGB")
for i in range(1):
    pack.load_image(im, 0)
    arr = pack.get_image()

pack._print_debug()
end = time.time()

print("Time:", end - start)