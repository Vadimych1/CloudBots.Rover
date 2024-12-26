import numpy, cv2
from openni import openni2
from miniros.source import Node
from miniros.builtin_datatypes import Image
import time
from PIL import Image as pilimg

openni2.initialize("openni_lib")

class StereoCam:
    def __init__(self, cam_index: int = None, initVideo = True) -> None:
        self.dev = openni2.Device.open_any()

        self.depth_stream = self.dev.create_depth_stream()
        self.ir_stream = self.dev.create_ir_stream()

        if initVideo:

            if cam_index:
                self.video_stream = cv2.VideoCapture(cam_index)
            else:
                self.video_stream = cv2.VideoCapture(0)

            self._cam_index = cam_index

            self.last_cam_ready = True

    def start_depth(self) -> None:
        self.depth_stream.start()
        # print(self.depth_stream.get_property(openni2.c_api.ONI_STREAM_PROPERTY_VERTICAL_FOV, openni2.c_api.ctypes.c_uint8))

    def start_ir(self) -> None:
        self.ir_stream.start()

    def stop_depth(self) -> None:
        self.depth_stream.stop()
        self.ir_stream.stop()

    def start_video(self) -> None:
        self.video_stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.video_stream.set(cv2.CAP_PROP_FPS, 30)
        self.video_stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.video_stream.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.video_stream.set(cv2.CAP_PROP_AUTO_WB, 0)
        self.video_stream.set(cv2.CAP_PROP_WB_TEMPERATURE, 0)
        self.video_stream.set(cv2.CAP_PROP_AUTOFOCUS, 0)

    def stop_video(self) -> None:
        self.video_stream.release()

    def get_depth(self) -> tuple[numpy.ndarray, numpy.ndarray]:
        """
        Get depth image from camera.
        use start_depth() before using
        """

        f = self.depth_stream.read_frame()

        buf = f.get_buffer_as_uint8()

        d_image = numpy.frombuffer(buf, dtype=numpy.uint8)
        d_image = d_image.reshape(f.height, f.width, 2)

        return d_image[:, :, 0], d_image[:, :, 1]
    
    def get_color(self) -> numpy.ndarray:
        """
        Get color image from camera.
        use start_video() before using
        """
        
        ret, frame = self.video_stream.read()
        self.last_cam_ready = ret

        frame = cv2.flip(frame, 1, frame)

        return frame

    def get_ir(self) -> tuple[numpy.ndarray, numpy.ndarray]:
        """
        Get IR image from camera.
        use start_ir() before using
        """

        q = self.ir_stream.read_frame()
        buf = q.get_buffer_as_uint8()
        frame = numpy.frombuffer(buf, dtype=numpy.uint8)
        frame = frame.reshape((q.height, q.width, 2))
        return frame[:,:,0], frame[:,:,1]

FPS = 20
if __name__ == "__main__":
    cam = StereoCam(0, initVideo = False)
    # cam = StereoCam(0)

    cam.start_depth()
    cam.start_ir()
    # cam.start_video()

    node = Node(4532, "stereocam")
    node.run()

    node.create_topic(Image(), "stereocam_depth")
    # node.create_topic(Image(), "stereocam_ir")

    t = time.time()
    while True:
        d1, d2 = cam.get_depth()
        # ir1, ir2 = cam.get_ir()
        # col = cam.get_color() # fix this

        try:
            pack = Image()
            
            im = pilimg.fromarray(d1, mode="L").convert("RGB")
            pack.load_image(im)
            node.publish(pack, "stereocam_depth")

            # im = pilimg.fromarray(ir1, mode="L").convert("RGB")
            # print(im)
            # pack.load_image(im)
            # node.publish(pack, "stereocam_ir")
        except Exception as e:
            print(e)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        q = time.time()
        print(q - t, "waiting")
        if (q - t) < 1/FPS:
            time.sleep(1/FPS - (q - t))

        t = q

    node.stop()
    
    # cam.stop_video()
    cam.stop_depth()
    cv2.destroyAllWindows()
    openni2.unload()