import argparse
import time
from miniros import source
from .stereocam import StereoCam
from .datatypes import Image
import cv2
from PIL import Image as pilimg

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=4532, help="Port number to use", metavar="<int>")
parser.add_argument("--no_stereocam_video_stream", action="store_true", default=False, help="Don`t run stereocam video stream")
parser.add_argument("--cam_index", type=int, default=0, help="Camera index to use", metavar="<int>")
parser.add_argument("--stereo", action="store_true", default=False, help="Create stereo camera publisher")
parser.add_argument("--prefix", type=str, default="", help="Prefix for topics and nodes", metavar="<str>")
parser.add_argument("--fps", type=int, default=30, help="FPS", metavar="<int>")
args = parser.parse_args()

if args.stereo:
    cam = StereoCam(args.cam_index, args.no_stereocam_video_stream)

    cam.start_depth()
    cam.start_ir()
    if not args.no_stereocam_video_stream:
        cam.start_video()

    node = source.Node(args.port, args.prefix + "stereocam")
    node.run()

    node.create_topic(Image(), args.prefix + "stereocam_depth")
    node.create_topic(Image(), args.prefix + "stereocam_ir")
    if not args.no_stereocam_video_stream:
        node.create_topic(Image(), args.prefix + "stereocam_video")

    t = time.time()
    while True:
        d1, d2 = cam.get_depth()
        ir1, ir2 = cam.get_ir()
        if not args.no_stereocam_video_stream:
            col = cam.get_color()

        try:
            pack = Image()

            if not args.no_stereocam_video_stream:
                pack.load_image(pilimg.fromarray(col).convert("RGB"))
                node.publish(pack, args.prefix + "stereocam_video")

            pack.load_image(pilimg.fromarray(d1).convert("RGB"))
            node.publish(pack, args.prefix + "stereocam_depth")

            pack.load_image(pilimg.fromarray(ir1).convert("RGB"))
            node.publish(pack, args.prefix + "stereocam_ir")

            if time.time() - t < 1.0 / args.fps:
                time.sleep(1.0 / args.fps - (time.time() - t))
            t = time.time()

        except KeyboardInterrupt:
            break
else:
    cam = cv2.VideoCapture(args.cam_index)
    node = source.Node(args.port, args.prefix + "cam")
    node.run()

    node.create_topic(Image(), args.prefix + "cam_video")

    t = time.time()
    while True:
        ret, frame = cam.read()

        try:
            pack = Image()
            pack.load_image(pilimg.fromarray(frame))
            node.publish(pack, args.prefix + "cam_video")

            if time.time() - t < 1.0 / args.fps:
                time.sleep(1.0 / args.fps - (time.time() - t))
            t = time.time()
        except KeyboardInterrupt:
            break