# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS 2 Jazzy + Gazebo Harmonic simulation of a 4-wheeled skid-steer rover. Documentation (README.md) is in Japanese.

## Build & Run

```bash
# Build (from workspace root)
cd ~/ros2_ws
colcon build --packages-select bme_simplerover_gazebo
source install/setup.bash

# Launch simulation
ros2 launch bme_simplerover_gazebo sim.launch.py

# Teleop control (separate terminal, requires interactive terminal)
source ~/ros2_ws/install/setup.bash
ros2 run bme_simplerover_gazebo teleop_key_node.py
```

## Lint / Test

```bash
# Run package tests (ament_lint_auto + ament_lint_common)
cd ~/ros2_ws
colcon test --packages-select bme_simplerover_gazebo
colcon test-result --verbose
```

## Architecture

**Simulation pipeline:** Xacro → robot_state_publisher → Gazebo spawn → ros_gz_bridge → fake_gnss_node

The launch file (`launch/sim.launch.py`) orchestrates everything in order:
1. Processes `urdf/rover.urdf.xacro` into a robot description
2. Starts Gazebo with `worlds/empty.sdf`
3. Publishes TF via robot_state_publisher (use_sim_time=true)
4. Spawns the rover entity in Gazebo at z=0.1m
5. Starts ros_gz_bridge with `config/bridge.yaml` for topic translation
6. Starts `fake_gnss_node` to publish ground-truth position as UTM/GnssSolution

**Robot model** (`urdf/rover.urdf.xacro`): Defines a skid-steer rover with `base_footprint` → `base_link` → 4 wheel links. Contains three Gazebo plugins:
- `DiffDrive`: Converts `/cmd_vel` Twist to wheel commands (left pair + right pair). Publishes wheel-based odometry on `odom`.
- `OdometryPublisher`: Publishes ground-truth odometry on `ground_truth_odom` directly from the physics engine pose (no wheel slip error).
- `JointStatePublisher`: Publishes wheel joint states.

**Topic bridge** (`config/bridge.yaml`): Maps between ROS 2 and Gazebo message types:
- `/cmd_vel` (ROS→GZ): velocity commands
- `/odom` (GZ→ROS): wheel-based odometry (subject to slip error during turns)
- `/ground_truth/odom` (GZ→ROS): physics engine ground-truth odometry
- `/tf`, `/joint_states` (GZ→ROS): transforms and joint state feedback

**Scripts** (`scripts/`):
- `fake_gnss_node.py`: Subscribes to `/ground_truth/odom`, publishes `bme_common_msgs/GnssSolution` on `/gnss/solution` with UTM coordinates. Uses configurable UTM origin parameters.
- `teleop_key_node.py`: Keyboard teleop (w/a/s/d/q/e). Publishes zero velocity when no key is pressed. Runs standalone (not in launch file).

## Key Conventions

- Build system: ament_cmake
- Robot parameters (dimensions, mass, friction) are defined as xacro properties at the top of `rover.urdf.xacro`
- All simulation uses `use_sim_time:=true`
- Odometry frame: `odom` → `base_footprint` at 30 Hz
- Heading follows REP-103: ENU convention (East=0°, North=90°, CCW positive), range -180° to 180°

## Gazebo Friction Notes

- Each wheel requires `<fdir1>1 0 0</fdir1>` to lock `mu1`/`mu2` to the wheel's local frame. Without this, friction directions are world-aligned and rotation behavior changes with robot orientation.
- `mu1` (rolling direction): high value for traction. `mu2` (lateral direction): low value to allow skid-steer turning.
- Adjusting `mu2` controls how easily the rover performs pivot turns.

## Terminal Raw Mode (teleop node)

- `teleop_key_node.py` uses `tty.setcbreak()` which disables terminal echo. Always use `atexit.register()` to guarantee terminal restoration on any exit path.
- Drain the stdin buffer fully on each tick (`while select(...)`) to avoid stale key lag when switching directions.
