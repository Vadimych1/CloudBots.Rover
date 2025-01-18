import random
import numpy as np
from filterpy.kalman import KalmanFilter

from movement.source import QuadMotorDriver
from lidar_module.source import Lidar

# ! Kalman filter: pos(x, y) -> pos(x, y), vel(x, y)
# kf = KalmanFilter(dim_x=4, dim_z=2)
# dt = 1.0  # time step

# # State transition matrix: [x, x_vel, y, y_vel]
# kf.F = np.array([[1, dt, 0, 0],
#                     [0, 1, 0, 0],
#                     [0, 0, 1, dt],
#                     [0, 0, 0, 1]])

# # Measurement function: [x_pos, y_pos]
# kf.H = np.array([[1, 0, 0, 0],
#                     [0, 0, 1, 0]])

# # Initial state estimate
# kf.x = np.array([0, 0, 0, 0])

# # Covariance matrices
# kf.P *= 1000.0  # initial uncertainty
# kf.R = np.array([[5, 0],
#                     [0, 5]])  # measurement noise
# kf.Q = np.array([[1, 0, 0, 0],
#                     [0, 1, 0, 0],
#                     [0, 0, 1, 0],
#                     [0, 0, 0, 1]])  # process noise

# ! Kalman filter: acc(x, y) -> acc(x, y), vel(x, y)
# kf = KalmanFilter(dim_x=4, dim_z=2)
# dt = 1.0  # time step

# # State transition matrix: [x, x_vel, y, y_vel]
# kf.F = np.array([[1, dt, 0, 0],
#                     [0, 1, 0, 0],
#                     [0, 0, 1, dt],
#                     [0, 0, 0, 1]])

# # Measurement function: [x_acc, y_acc]
# kf.H = np.array([[1, 0, 0, 0],
#                     [0, 0, 1, 0]])

# # Initial state estimate
# kf.x = np.array([0, 0, 0, 0])

# # Covariance matrices
# kf.P *= 1000.0  # initial uncertainty
# kf.R = np.array([[5, 0],
#                     [0, 5]])  # measurement noise
# kf.Q = np.array([[1, 0, 0, 0],
#                     [0, 1, 0, 0],
#                     [0, 0, 1, 0],
#                     [0, 0, 0, 1]])  # process noise