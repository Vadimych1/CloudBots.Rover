from miniros.builtin_datatypes import Image
import numpy as np
import PIL.Image as pilimg

im = Image()
im.load_image(pilimg.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)))

print(len(im.convert_additional_data() + str(im).encode()))