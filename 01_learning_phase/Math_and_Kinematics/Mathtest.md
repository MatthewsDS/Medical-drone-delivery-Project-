Plaintext
## 🛸 Drone Kinematics Reference

### 1. 3D Rotation Matrix for Pitch
To handle the drone's tilt in mid-air, we use this 3D rotation matrix:

$$
R_x(\theta) = \begin{bmatrix} 1 & 0 & 0 \\ 0 & \cos\theta & -\sin\theta \\ 0 & \sin\theta & \cos\theta \end{bmatrix}
$$

### 2. Angular Acceleration Equation
$$ \tau = I \cdot \alpha $$
