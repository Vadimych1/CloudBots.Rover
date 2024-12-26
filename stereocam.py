import numpy, cv2
import os
# import colorama as cr
from openni import openni2

LAST_TEXT_W = 0
def qprint(text):
    global LAST_TEXT_W

    print("\r" + text + " " * (LAST_TEXT_W - len(text)), end="")
    LAST_TEXT_W = len(text)

OPENNI_INCLUDE = os.getenv("OPENNI2_INCLUDE")
OPENNI_REDIST = os.getenv("OPENNI2_REDIST")

qprint("Initializing")
# openni2.initialize(*(OPENNI_INCLUDE, OPENNI_REDIST,) if OPENNI_INCLUDE and OPENNI_REDIST else openni2._default_dll_directories)
openni2.initialize()

class StereoCam:
    def __init__(self, cam_index: int = None, initVideo = True) -> None:
        qprint("Open device")
        self.dev = openni2.Device.open_any()

        qprint("Stream: Depth")
        self.depth_stream = self.dev.create_depth_stream()
        qprint("Stream: IR")
        self.ir_stream = self.dev.create_ir_stream()

        if initVideo:
            qprint("Stream: Video") 

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

if __name__ == "__main__":
    qprint("Creating cam")

    cam = StereoCam(0, initVideo = False)
    # cam = StereoCam(0)

    qprint("Starting streams")
    cam.start_depth()
    cam.start_ir()
    # cam.start_video()

    qprint("Started")

    while True:

        d1, d2 = cam.get_depth()
        ir1, ir2 = cam.get_ir()
        # col = cam.get_color()

        try:
            cv2.imshow("Depth 1", d1)
            cv2.imshow("Depth 2", d2)
            cv2.imshow("IR1", ir1)
            cv2.imshow("IR2", ir2)
            # cv2.imshow("Video", col)

        except:
            pass

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    qprint("Quit")
    
    # cam.stop_video()
    cam.stop_depth()
    cv2.destroyAllWindows()
    openni2.unload()