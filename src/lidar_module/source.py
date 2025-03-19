# from rplidar import RPLidar, RPLidarException
import numpy as np
from cv2.typing import MatLike
import logging
from typing import Generator
import cv2 as cv
import sys
from sklearn.neighbors import NearestNeighbors
from scipy.optimize import minimize


class SLAM:
    """
    Custom SLAM class

    :param initial_state: the first data frame from LiDAR
    :type initial_state: MatLike
    """
    def __init__(self, initial_state: MatLike = None) -> None:
        self.pos = np.array([0.0, 0.0, 0.0])
        self.prevstate = initial_state

        self.result = None
        self.error = None

    def update(self, newstate: MatLike) -> None:
        """
        Apply a new transform by SLAM

        :param newstate: a new LiDAR state
        :type newstate: MatLike
        """

        if self.prevstate is None:
            self.prevstate = newstate
            return

        aligned_points = self.prevstate
        newstate_points = newstate

        transform, error = self.icp(aligned_points, newstate_points, 5000)

        dx, dy = transform[0, 2], transform[1, 2]
        phi = np.arcsin(transform[0, 1])

        self.pos[0] += dx
        self.pos[1] += dy
        self.pos[2] += phi

        self.pos[2] = self.pos[2] % (2 * np.pi)

        # Store results
        self.prevstate = newstate
        self.result = transform
        self.error = error

    def icp(self, a, b, n_iters: int = 60) -> np.ndarray[np.float64]:
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

        for _ in range(n_iters):
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
    def csm(self, a, b, search_radius=10, angle_range=np.pi/6, angle_step=np.pi/90, resolution=1.0) -> np.ndarray[np.float64]:
        """
        Implementation of Correlative Scan Matching algorithm

        :param a: previous scan
        :type a: MatLike

        :param b: current scan
        :type b: MatLike

        :param search_radius: maximum search radius in pixels
        :type search_radius: float

        :param angle_range: maximum rotation angle to search (in radians)
        :type angle_range: float

        :param angle_step: step size for rotation search (in radians)
        :type angle_step: float

        :param resolution: grid resolution for matching
        :type resolution: float

        :return: transformation matrix and error
        :rtype: tuple[ndarray[float64], float]
        """
        # convert point clouds to grid representation
        def points_to_grid(points, resolution, padding):
            min_x, min_y = np.min(points[:, 0]) - padding, np.min(points[:, 1]) - padding
            max_x, max_y = np.max(points[:, 0]) + padding, np.max(points[:, 1]) + padding
            width = int((max_x - min_x) / resolution) + 1
            height = int((max_y - min_y) / resolution) + 1
            grid = np.zeros((height, width), dtype=np.uint8)
            for point in points:
                x, y = point
                grid_x = int((x - min_x) / resolution)
                grid_y = int((y - min_y) / resolution)
                if 0 <= grid_x < width and 0 <= grid_y < height:
                    grid[grid_y, grid_x] = 1

            return grid, (min_x, min_y, resolution)

        # create distance transform from grid
        def create_distance_transform(grid):
            dist_transform = cv.distanceTransform(1 - grid, cv.DIST_L2, 3)
            return dist_transform
        
        # score a transformation
        def score_transform(src_points, dst_dist_transform, transform_params, grid_info):
            min_x, min_y, res = grid_info
            
            # create transformation matrix
            dx, dy, theta = transform_params
            T = np.array([
                [np.cos(theta), -np.sin(theta), dx],
                [np.sin(theta), np.cos(theta), dy],
                [0, 0, 1]
            ])
            
            # apply transformation
            n = src_points.shape[0]
            homogeneous_points = np.ones((n, 3))
            homogeneous_points[:, :2] = src_points
            transformed_points = (homogeneous_points @ T.T)[:, :2]
            
            grid_points = np.zeros_like(transformed_points)
            grid_points[:, 0] = (transformed_points[:, 0] - min_x) / res
            grid_points[:, 1] = (transformed_points[:, 1] - min_y) / res
            
            # apply to nearest grid cell
            grid_points = np.round(grid_points).astype(np.int32)
            
            # filter invalid
            valid_indices = (
                (grid_points[:, 0] >= 0) & 
                (grid_points[:, 0] < dst_dist_transform.shape[1]) & 
                (grid_points[:, 1] >= 0) & 
                (grid_points[:, 1] < dst_dist_transform.shape[0])
            )
            
            valid_points = grid_points[valid_indices]
            
            if len(valid_points) == 0:
                return float('inf')
            
            # calc distances
            distances = dst_dist_transform[valid_points[:, 1], valid_points[:, 0]]
            
            # calc score
            score = np.mean(distances)
            return score
        
        src_points = a.copy().T
        dst_points = b.copy().T
        
        # grid & dist transforms
        padding = search_radius * resolution
        dst_grid, grid_info = points_to_grid(dst_points, resolution, padding)
        dst_dist_transform = create_distance_transform(dst_grid)
        
        best_score = float('inf')
        best_transform = np.eye(3)
        
        x_range = np.arange(-search_radius, search_radius + 1, resolution)
        y_range = np.arange(-search_radius, search_radius + 1, resolution)
        theta_range = np.arange(-angle_range, angle_range + angle_step, angle_step)
        
        # search for the best transformation
        for theta in theta_range:
            for dx in x_range[::2]:
                for dy in y_range[::2]:
                    score = score_transform(src_points, dst_dist_transform, (dx, dy, theta), grid_info)
                    if score < best_score:
                        best_score = score
                        best_transform = np.array([
                            [np.cos(theta), -np.sin(theta), dx],
                            [np.sin(theta), np.cos(theta), dy],
                            [0, 0, 1]
                        ])
        
        # calc best transform
        dx_best, dy_best = best_transform[0, 2], best_transform[1, 2]
        theta_best = np.arctan2(best_transform[1, 0], best_transform[0, 0])
        
        refined_x_range = np.arange(dx_best - resolution, dx_best + resolution + 0.1, resolution/2)
        refined_y_range = np.arange(dy_best - resolution, dy_best + resolution + 0.1, resolution/2)
        refined_theta_range = np.arange(theta_best - angle_step, theta_best + angle_step + 0.01, angle_step/2)
        
        # full search for the best transformation
        for theta in refined_theta_range:
            for dx in refined_x_range:
                for dy in refined_y_range:
                    score = score_transform(src_points, dst_dist_transform, (dx, dy, theta), grid_info)
                    if score < best_score:
                        best_score = score
                        best_transform = np.array([
                            [np.cos(theta), -np.sin(theta), dx],
                            [np.sin(theta), np.cos(theta), dy],
                            [0, 0, 1]
                        ])
        
        return best_transform, best_score


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
        
        self.slam = SLAM(np.array([]))
        self.running = False


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

                    dx, dy, dr = self.slam.pos
                    x, y = dx + distance * np.cos(np.deg2rad(angle + dr)), dy + distance * np.sin(np.deg2rad(angle + dr))
                    c += 1

                    if c % 100 == 0:
                        if self.slam.prevstate == None:
                            self.slam.prevstate = np.array(scans)
                        else:
                            self.slam.update(np.array(scans))
                        
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


if __name__ == "__main__":
    x1 = np.array([[x for x in range(0, 100)], [4 for x in range(0, 100)]])
    y1 = np.array([[x for x in range(0, 100)], [99 - x for x in range(0, 100)]])
    y2 = np.array([[x for x in range(0, 100)], [4 for x in range(0, 100)]])
    # y2 = np.array([[4 for x in range(0, 100)], [x for x in range(0, 100)]])

    s = SLAM(x1)

    # s.update(y1)
    # print(s.error, s.pos[:2], np.rad2deg(s.pos[2]))

    s.update(y1)
    print(s.error, s.pos[:2], np.rad2deg(s.pos[2]))
    s.update(y2)
    print(s.error, s.pos[:2], np.rad2deg(s.pos[2]))