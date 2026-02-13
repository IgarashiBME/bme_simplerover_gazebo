# bme_simplerover_gazebo

Gazebo Harmonic 上で動作するシンプルなスキッドステアローバーのシミュレーション環境です。

## 前提条件

- **ROS 2**: Jazzy
- **Gazebo**: Harmonic (gz-harmonic)

### 依存パッケージのインストール

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-xacro \
  ros-jazzy-teleop-twist-keyboard
```

## ビルド

```bash
cd ~/ros2_ws
colcon build --packages-select bme_simplerover_gazebo
source install/setup.bash
```

## 起動

```bash
ros2 launch bme_simplerover_gazebo sim.launch.py
```

Gazebo GUI が起動し、ローバーがスポーンされます。

## 操縦テスト

別ターミナルで teleop_twist_keyboard を起動します:

```bash
source ~/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

キーボード操作:
- `i` : 前進
- `,` : 後退
- `j` : 左旋回
- `l` : 右旋回
- `k` : 停止

## トピック一覧

| トピック | 型 | 方向 |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS 2 -> Gazebo |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo -> ROS 2 |
| `/tf` | `tf2_msgs/msg/TFMessage` | Gazebo -> ROS 2 |
| `/joint_states` | `sensor_msgs/msg/JointState` | Gazebo -> ROS 2 |

## 動作確認

```bash
# トピック確認
ros2 topic list

# odom の確認
ros2 topic echo /odom

# cmd_vel を直接 publish
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.3}}"
```
