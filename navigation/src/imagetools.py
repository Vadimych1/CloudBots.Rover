import requests, json
from PIL import Image
import logging
import threading
import time, glob, os, sys, tqdm
import cv2 as cv
import numpy as np

logging.basicConfig(level=logging.INFO)

class PanoramaViewer:
    """
    Base class for panorama segmentation.
    """
    def __init__(self, panoramaImage: Image.Image):
        """
        ::param:: panoramaImage: Image.Image - 360 panorama.
        """
        self.image = panoramaImage

    def _slice(self, start_degree: int, end_degree: int) -> Image.Image:
        """
        Slice 360 panorama image between ::param:: start_degree and ::param:: end_degree.
        """
        per_deg = 360 / self.image.width
        start = int(start_degree / per_deg)
        end = int(end_degree / per_deg)
        return self.image.crop((start, 0, end, self.image.height))
    
    def _remesh(self, image: Image.Image, k1: float = -0.1, k2: float = 0.05):
        """
        Remove distortions from panorama segment (radial & tangential).
        """
        # TODO: change k1 & k2 to fit
        # convert to cv2 image
        im = np.array(image)

        h, w, _ = im.shape

        # define cam matrix for undistort
        camera_matrix = np.array([
            [w / 2, 0, w / 2],
            [0, h / 2, h / 2],
            [0, 0, 1]    
        ])

        # define distortion coeffs
        dist_coeffs = np.array([k1, k2, 0, 0])

        # undistort
        im = cv.undistort(im, camera_matrix, dist_coeffs)

        return Image.fromarray(im)
    
    def show(self, start_degree: int, end_degree: int):
        """
        Show panorama segment between ::param:: start_degree and ::param:: end_degree.
        """
        im = self._slice(start_degree, end_degree)
        im3 = self._remesh(im)
        im3.show()

    def get(self, start_degree: int, end_degree: int):
        """
        Get panorama segment between ::param:: start_degree and ::param:: end_degree.
        """
        im = self._slice(start_degree, end_degree)
        return self._remesh(im)

class YandexPanoramaLoader:
    def _start_download(self, url: str, path: str, id: str) -> tuple[Image.Image, bool]:
        """
        Download image.
        """
        try:
            data = requests.get(f"{url}/{path}/{id}")
            with open(f"cache/{path}.{id}.png", "wb") as f:
                f.write(data.content)
            return Image.open(f"cache/{path}.{id}.png"), True
        
        except Exception as e:
            return Image.new("RGB", (256, 256), "black"), False

    def _yamap_row_download(self, url: str, path: str, row: int, id_from: int = 0, id_to: int = 25, part: int = 0) -> list[Image.Image]:
        """
        Download one row from pano.
        ::param:: id_from - min id to start with
        ::param:: id_to - max id to download
        ::param:: part - like resolution
        """
        images = []
        for i in range(id_from, id_to + 1, 1):
            im, r = self._start_download(url, path, f"{part}.{str(row)}.{str(i)}")

            # break if download failed (means this tile was last)
            if not r:
                break
            images.append(im)
        return images

    def load_yamaps_panorama(self, panoID: str, max_row: int = 32, type: int = 0) -> list[list[Image.Image]]:
        """
        Load pano from YandexMaps with params. Returns matrix of images.
        """
        # define pano tows list
        p = [[] for _ in range(max_row + 1)]
        self.counter = 0

        # download function for async download
        def _load(i):
            p[i] = self._yamap_row_download("https://pano.maps.yandex.net", panoID, i, 0, 30, type)
            self.counter += 1
        
        # start download threads
        for i in range(max_row + 1):
            t = threading.Thread(target=_load, args=(i,))
            t.start()

        # wait for all downloads to end
        while self.counter < (max_row + 1):
            time.sleep(0.1)

        # filter empty values
        d = []
        for i in p:
            d.append(i) if len(i) > 0 else None

        return d

    def download(self, panoID: str, quality: int = 3, pos: str = "0.0,0.0") -> Image.Image:
        """
        Download image from panoID. Returns image.
        """

        if f"{pos}.png" in os.listdir("datasets/raw"):
            print("Found downloaded image")
            return Image.open(f"datasets/raw/{pos}.png")
        
        # load panorama fragments
        panorama_files = self.load_yamaps_panorama(panoID, type=quality)
        
        # get size of first fragment (usually 256x256)
        size = panorama_files[0][0].size
        
        # create new image where all fragments will be pasted
        image2 = Image.new("RGB", (size[0] * len(panorama_files), size[1] * len(panorama_files[0])), "white")
        
        x = 0
        for img in tqdm.tqdm(panorama_files):
            y = 0
            for i in img:
                image2.paste(i, (x * size[1], y * size[0]))
                y += 1
            x += 1

        return image2

    def try_download(self, panoID: str, quality: int = 3, pos: str = "0.0,0.0") -> Image.Image:
        """
        Try to download pano, if failed, return white image.
        """
        try:
            return self.download(panoID, quality, pos)
        except Exception as e:
            print("Error downloading", panoID, "::", e)
            return Image.new("RGB", (256, 256), "white")

    def remove_cached(self):
        """
        Remove image files used to create panorama from './cache/'
        """
        for f in glob.glob("cache/*.png"):
            try:
                os.remove(f)
            except:
                pass

    def download_from_file(self, input: str, type=2):
        """
        Download images from json file with panoId`s and points
        """
        for d in json.load(open(input, "r")):
            id = d["id"]
            print("Downloading", id)

            yield {"image": self.try_download(id, type, d["point"]), "id": id, "pos": d["point"]}

def process_image(image, save = True, inThread = False):
    """
    Process pano image (crop 360 panorama to pieces)
    """
    global threads

    # save if need
    if save: image["image"].save(f"datasets/raw/{image["pos"]}.png")
    # create viewer
    pan = PanoramaViewer(image["image"])

    # slice
    done_panoramas = os.listdir(f"datasets/sliced/")
    for i in range(0, int((360 - w) + every/2), every):
        img = None
        if f"{image['pos']}_{i}.png" in done_panoramas:
            print("Found already sliced image: ", i)     
            img = Image.open(f"datasets/sliced/{image['pos']}_{i}.png")
        else:
            img = pan.get(i, i + w)
            img.save(f"datasets/sliced/{image['pos']}_{i}.png")

        dataset.append({"image": f"datasets/sliced/{image['pos']}_{i}.png", "start_angle": i, "end_angle": i + w, "pos": image["pos"]})

    if inThread:
        threads -= 1

def async_process_image(image, save = True):
    """
    Async process pano image (with treading)
    """
    global threads, max_threads
    while threads >= max_threads:
        time.sleep(0.05)

    threads += 1
    thread = threading.Thread(target=process_image, args=(image, save, True))
    thread.start()

w = int(360/4) # ! image width
every = int(w/2) # ! step
dataset = [] # ! cropped panoramas
loader = None # ! panorama loader

max_threads = 8 # ! max threads to use (may speed up processing)
threads = 0 # ! current threads. Do not change

if __name__ == "__main__":
    # parse
    try:
        if len(sys.argv) <= 1:
            print("Parsing from Yandex...")

            loader = YandexPanoramaLoader()

            for image in loader.download_from_file("parseddata/panoramas.json", type=0):
                async_process_image(image)

            loader.remove_cached()
        else:
            print("Loading from", sys.argv[1])    
            
            for image, path in [(Image.open(path), path) for path in glob.glob(f"{sys.argv[1]}/*.png")]:
                print("Processing", path)
                ppath = ".".join(path.split("\\")[-1].split(".")[:-1])

                async_process_image({"image": image, "pos": ppath}, False)

    except Exception as e:
        print("Error, parsing from Yandex ||", e)

        loader = YandexPanoramaLoader()

        for image in loader.download_from_file("parseddata/panoramas.json", type=0):
            async_process_image(image)

        loader.remove_cached()

    with open("datasets/sliced/dataset.json", "w") as f:
            json.dump(dataset, f)