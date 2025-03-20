from rplidar import RPLidar, RPLidarException
import numpy as np
from cv2.typing import MatLike
import logging
from typing import Generator
import cv2 as cv
import sys
from sklearn.neighbors import NearestNeighbors
from scipy.optimize import minimize
import time


class SLAM:
    """
    Custom SLAM class

    :param initial_state: the first data frame from LiDAR
    :type initial_state: MatLike
    """
    def __init__(self, initial_state: MatLike = None, search_radius: int = 2000) -> None:
        self.pos = np.array([0.0, 0.0, 0.0])            

        self.result = None
        self.error = None

        self.map = np.zeros((20000, 20000), dtype=np.uint16)
        self.search_radius = search_radius

        d = np.array([self.map.shape[0] / 2, self.map.shape[1] / 2])
        for p in initial_state.T:
            ind = (p + d).astype(np.uint16)
            self.map[ind[0], ind[1]] = 255


    def _grid2dots(self, x1, y1, x2, y2):
        x1 += int(self.map.shape[0]/2)
        x2 += int(self.map.shape[0]/2)
        y1 += int(self.map.shape[1]/2)
        y2 += int(self.map.shape[1]/2)
        
        g = self.map[x1:x2, y1:y2]
        points = []

        for y in range(g.shape[0]):
            for x in range(g.shape[1]):
                if g[y, x] == 255:
                    points.append((x, y))

        return np.array(points).T


    def update(self, newstate: MatLike) -> None:
        """
        Apply a new transform by SLAM

        :param newstate: a new LiDAR state
        :type newstate: MatLike
        """

        dx, dy, _ = self.pos
        aligned_points = self._grid2dots(int(dx - self.search_radius), int(dy - self.search_radius), 
                                         int(dx + self.search_radius), int(dy + self.search_radius),
        )
        newstate_points = newstate

        print(aligned_points.shape, newstate_points.shape)
        transform, error = self.icp(aligned_points, newstate_points)

        ndx, ndy = transform[0, 2], transform[1, 2]
        phi = np.arcsin(transform[0, 1])

        self.pos[0] += ndx
        self.pos[1] += ndy
        self.pos[2] += phi
        self.pos[2] = self.pos[2] % (2 * np.pi)

        delta = np.array([ndx - dx, ndy - dy])
        for p in newstate_points.T:
            ind = p - delta
            self.map[int(ind[0]), int(ind[1])] = 255

        self.result = transform
        self.error = error

    def icp(self, a, b, n_iters: int = 500) -> np.ndarray[np.float64]:
        """
        Implementation of Iterative Closest Point algorithm

        :param a: previous scan
        :type a: MatLike

        :param b: current scan
        :type b: MatLike

        :param n_iters: number of iterations
        :type c: int

        :return: delta x, y and phi (rotation)
        :rtype: ndarray[float64]
        """
        def res(p, src, dst):
            # transform matrix
            T = np.matrix(
                [
                    [np.cos(p[2]), -np.sin(p[2]), p[0]],
                    [np.sin(p[2]), np.cos(p[2]), p[1]],
                    [0, 0, 1],
                ]
            )

            # apply transform to src
            n = src.shape[0]
            xt = np.ones([n, 3])
            xt[:, :-1] = src
            xt = (xt * T.T).A

            # calculate remainder
            d = np.zeros(src.shape)
            d[:, 0] = xt[:, 0] - dst[:, 0]
            d[:, 1] = xt[:, 1] - dst[:, 1]
            r = np.sum(d[:, 0] ** 2 + d[:, 1] ** 2)

            return r

        # Jacobian gradient
        def jac(p, src, dst):
            # calc transform
            T = np.matrix(
                [
                    [np.cos(p[2]), -np.sin(p[2]), p[0]],
                    [np.sin(p[2]), np.cos(p[2]), p[1]],
                    [0, 0, 1],
                ]
            )
            n = src.shape[0]
            xt = np.ones([n, 3])
            xt[:, :-1] = src
            xt = (xt * T.T).A
            d = np.zeros(src.shape)
            
            d[:, 0] = xt[:, 0] - dst[:, 0]
            d[:, 1] = xt[:, 1] - dst[:, 1]

            dUdth_R = np.matrix(
                [
                    [-np.sin(p[2]), -np.cos(p[2])],
                    [np.cos(p[2]), -np.sin(p[2])],
                ]
            )
            dUdth = (src * dUdth_R.T).A
            
            g = np.array(
                [
                    np.sum(2 * d[:, 0]),
                    np.sum(2 * d[:, 1]),
                    np.sum(2 * (d[:, 0] * dUdth[:, 0] + d[:, 1] * dUdth[:, 1])),
                ]
            )
            
            return g

        # Hessian matrix
        def hess(p, src, dst):
            n = src.shape[0]
            
            # transform
            T = np.matrix(
                [
                    [np.cos(p[2]), -np.sin(p[2]), p[0]],
                    [np.sin(p[2]), np.cos(p[2]), p[1]],
                    [0, 0, 1],
                ]
            )
            
            n = src.shape[0]
            xt = np.ones((n, 3))
            
            xt[:, :-1] = src
            xt = (xt * T.T).A
            
            d = np.zeros(src.shape)
            d[:, 0] = xt[:, 0] - dst[:, 0]
            d[:, 1] = xt[:, 1] - dst[:, 1]
            
            dUdth_R = np.matrix(
                [
                    [-np.sin(p[2]), -np.cos(p[2])],
                    [np.cos(p[2]), -np.sin(p[2])],
                ]
            )
            
            dUdth = (src * dUdth_R.T).A
            H = np.zeros([3, 3])
            
            H[0, 0] = n * 2
            H[0, 2] = np.sum(2 * dUdth[:, 0])
            H[1, 1] = n * 2
            H[1, 2] = np.sum(2 * dUdth[:, 1])
            H[2, 0] = H[0, 2]
            H[2, 1] = H[1, 2]
            
            d2Ud2th_R = np.matrix(
                [
                    [-np.cos(p[2]), np.sin(p[2])],
                    [-np.sin(p[2]), -np.cos(p[2])],
                ]
            )
            
            d2Ud2th = (src * d2Ud2th_R.T).A
            H[2, 2] = np.sum(
                2
                * (
                    np.square(dUdth[:, 0])
                    + np.square(dUdth[:, 1])
                    + d[:, 0] * d2Ud2th[:, 0]
                    + d[:, 0] * d2Ud2th[:, 0]
                )
            )

            return H

        init_pose = (0, 0, 0)
        src = np.array([a.T], copy=True).astype(np.float32)
        dst = np.array([b.T], copy=True).astype(np.float32)

        Tr = np.array(
            [
                [np.cos(init_pose[2]), -np.sin(init_pose[2]), init_pose[0]],
                [np.sin(init_pose[2]), np.cos(init_pose[2]), init_pose[1]],
                [0, 0, 1],
            ]
        )

        src = cv.transform(src, Tr[0:2])
        p_opt = np.array(init_pose, dtype=np.float64)
        T_opt = np.array([])
        error_max = sys.maxsize

        # for _ in range(n_iters):
        starttime = time.time()

        while time.time() - starttime < 2:
            _, indices = (
                NearestNeighbors(n_neighbors=1, algorithm="auto", p=3)
                .fit(dst[0])
                .kneighbors(src[0])
            )

            # minimize error
            p = minimize(
                res,
                [0, 0, 0],
                args=(src[0], dst[0, indices.T][0]),
                method="Newton-CG",
                jac=jac,
                hess=hess,
            ).x

            # apply transform
            T = np.array(
                [
                    [np.cos(p[2]), -np.sin(p[2]), p[0]],
                    [np.sin(p[2]), np.cos(p[2]), p[1]],
                ]
            )

            p_opt[:2] = (p_opt[:2] * np.matrix(T[:2, :2]).T).A
            p_opt += p
            
            src = cv.transform(src, T)
            Tr = (np.matrix(np.vstack((T, [0, 0, 1]))) * np.matrix(Tr)).A
            error = res([0, 0, 0], src[0], dst[0, indices.T][0])

            if error < error_max:
                error_max = error
                T_opt = Tr

        p_opt[2] = p_opt[2] % (2 * np.pi) # 0 <= p_opt[2] <= 2pi

        return T_opt, error_max
    
    # not working
    def csm(self, a, b, search_radius=300, angle_range=np.pi/6, angle_step=np.pi/90, resolution=1.0) -> np.ndarray[np.float64]:
        def evaluate_correlation(transformed_a, b):
            # Ensure transformed_a and b are 2D arrays with the same number of columns
            if transformed_a.shape[1] != b.shape[1]:
                raise ValueError("transformed_a and b must have the same number of columns")

            # Example correlation evaluation using nearest neighbors
            nbrs = NearestNeighbors(n_neighbors=1, algorithm='auto').fit(b)
            distances, _ = nbrs.kneighbors(transformed_a)
            score = -np.sum(distances)  # Negative sum of distances as a simple score
            return score

        best_score = -np.inf
        best_transform = None

        # Define the search space
        for dx in np.arange(-search_radius, search_radius, resolution):
            for dy in np.arange(-search_radius, search_radius, resolution):
                for dtheta in np.arange(-angle_range, angle_range, angle_step):
                    # Create transformation matrix
                    T = np.array([
                        [np.cos(dtheta), -np.sin(dtheta), dx],
                        [np.sin(dtheta), np.cos(dtheta), dy],
                        [0, 0, 1]
                    ])

                    # Apply transformation
                    transformed_a = cv.transform(np.array([a.T]), T[:2])[0]

                    # Ensure transformed_a is a 2D array with two columns
                    transformed_a = transformed_a.reshape(-1, 2)

                    # Evaluate correlation (e.g., using a simple distance metric)
                    score = evaluate_correlation(transformed_a, b)

                    # Update best score and transformation
                    if score > best_score:
                        best_score = score
                        best_transform = T

        return best_transform


    def fsm(self, a, b, feature_threshold=0.1, search_radius=300, angle_range=np.pi/6, angle_step=np.pi/90, resolution=1.0) -> np.ndarray[np.float64]:
        def extract_features(points):
            # Example feature extraction using corner detection
            # Convert points to an image-like format for feature detection
            img = np.zeros((1000, 1000), dtype=np.uint8)
            for x, y in points[0]:
                img[int(y) % 1000, int(x) % 1000] = 255

            # Detect corners using Harris Corner Detection
            corners = cv.cornerHarris(img, 2, 3, 0.04)
            features = np.argwhere(corners > feature_threshold * corners.max())
            return features

        def evaluate_feature_correlation(features_a, features_b):
            # Example correlation evaluation using nearest neighbors
            nbrs = NearestNeighbors(n_neighbors=1, algorithm='auto').fit(features_b)
            distances, _ = nbrs.kneighbors(features_a)
            score = -np.sum(distances)  # Negative sum of distances as a simple score
            return score

        a = np.array([a.T], copy=True)
        b = np.array([b.T], copy=True)

        best_score = -np.inf
        best_transform = None

        # Extract features from both scans
        features_a = extract_features(a)
        features_b = extract_features(b)

        # Define the search space
        for dx in np.arange(-search_radius, search_radius, resolution):
            for dy in np.arange(-search_radius, search_radius, resolution):
                for dtheta in np.arange(-angle_range, angle_range, angle_step):
                    # Create transformation matrix
                    T = np.array([
                        [np.cos(dtheta), -np.sin(dtheta), dx],
                        [np.sin(dtheta), np.cos(dtheta), dy],
                        [0, 0, 1]
                    ])

                    # Apply transformation to features
                    transformed_features_a = cv.transform(np.array([features_a]), T[:2])[0]

                    # Evaluate feature correlation
                    score = evaluate_feature_correlation(transformed_features_a, features_b)

                    # Update best score and transformation
                    if score > best_score:
                        best_score = score
                        best_transform = T

        return best_transform

class Lidar:
    """
    Class for lidar scanning

    :param port: the USB port of lidar. Default: "/dev/ttyUSB0"
    :param fallback_ports: ports to check if lidar os not on the default port
    """
    def __init__(self, port: str = "/dev/ttyUSB0", fallback_ports=["/dev/tty0"]):
        self.logger = logging.getLogger(f"Lidar[{port}]")
        try:
            self.lidar = RPLidar(port)
        except:
            for i, fallback in enumerate(fallback_ports):
                try:
                    self.lidar = RPLidar(fallback, 115200, 3)
                    break
                except:
                    if i == len(fallback_ports) - 1:
                        self.logger.error("Cannot connect to lidar, all fallbacks failed. Check if lidar connected or correct address.")
                        quit(1)

        self.running = False
        self.initializing = True

        self.logger.info("Initializing SLAM")

        init_vals = []
        iter = self.scan()
        for i in range(200):
            init_vals.append(next(iter))

        self.slam = SLAM(np.array(init_vals).T)
        self.initializing = False

        self.logger.info("Initialized")

        self.stop()

    def health(self):
        """
        Returns lidar health
        """
        return self.lidar.get_health()


    def info(self):
        """
        Returns lidar info
        """
        return self.lidar.get_info()
    

    def samplerate(self):
        """
        Returns lidar samplerate
        """
        return self.lidar.get_samplerate()
    

    def scan_modes(self):
        """
        Returns all lidar scan modes
        """
        return self.lidar.get_scan_modes()
    

    def scan(self, buffer: int = 10000) -> Generator[tuple[int, int], None, None]:
        """
        Start scan

        Yields every scan value

        :yields: tuple[x, y]
        """

        self.running = True
        
        while self.running:
            self.logger.info("Scan started")
            scans = []
            c = 0
            
            try:
                for data in self.lidar.iter_measures(max_buf_meas=buffer):
                    _, _, angle, distance = data
                    if distance <= 0:
                        continue
                    
                    dx, dy, dr = (0.0, 0.0, 0.0) if self.initializing else self.slam.pos
                    x, y = dx + distance * np.cos(np.deg2rad(angle + dr)), dy + distance * np.sin(np.deg2rad(angle + dr))
                    c += 1

                    if not self.initializing:
                        if (c + 1) % 600 == 0:
                            self.slam.update(np.array(scans).T)
                            print(self.slam.pos)
                            scans = []

                        if c % 301 == 0:   
                            self.lidar.clean_input()
                        elif c % 60001 == 0:
                            raise RPLidarException()
                        
                        scans.append([x, y])

                    yield x, y
                    
            except RPLidarException as e:
                self.lidar.stop()
                self.lidar.disconnect()
                self.lidar.connect()
            
            except Exception as e:
                self.logger.exception(e)
       
    def stop(self) -> None:
        """
        Stop lidar
        """     
        self.running = False
        self.logger.debug("Scan stopped")
        self.lidar.stop_motor()
        self.lidar.stop()





# if __name__ == "__main__":
#     x1 = np.array([[x for x in range(0, 100)], [4 for x in range(0, 100)]])
#     y1 = np.array([[x for x in range(0, 100)], [99 - x for x in range(0, 100)]])
#     y2 = np.array([[x for x in range(0, 100)], [4 for x in range(0, 100)]])
#     # y2 = np.array([[4 for x in range(0, 100)], [x for x in range(0, 100)]])

#     s = SLAM(x1)

#     # s.update(y1)
#     # print(s.error, s.pos[:2], np.rad2deg(s.pos[2]))

#     s.update(y1)
#     print(s.error, s.pos[:2], np.rad2deg(s.pos[2]))
#     s.update(y2)
#     print(s.error, s.pos[:2], np.rad2deg(s.pos[2]))

if __name__ == "__main__":
    l = Lidar()
    
    print("Running")

    i = 0 
    p = []
    q = []
    for x in l.scan():
        q.append(x)

        if i % 600 == 0:
            p.append(q)
            q = []

        if i == 600 * 2:
            break

        i += 1

    l.stop()

    import json
    json.dump(p, open("./data.json", "w"))
    json.dump(l.slam._grid2dots(-20000, -20000, 20000, 20000).tolist(), open("./map.json", "w"))