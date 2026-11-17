# Nav2 autonomous navigation guide

This package keeps the original Gazebo Fortress simulation and adds ROS 2 Humble Nav2 localization, global planning, local obstacle avoidance, and goal navigation.

## Navigation design

- **Localization:** AMCL estimates `map -> odom` using `/scan` and `/odom`.
- **Global planner:** NavFn with A* enabled plans through `maps/small_maze.yaml`.
- **Local controller:** DWB samples velocity trajectories and scores them against the global path and local costmap.
- **Obstacle sensing:** the LiDAR `/scan` feeds obstacle layers in both global and local costmaps. `marking` adds newly observed obstacles; `clearing` removes cells when laser rays show free space.
- **Recovery/replanning:** Nav2's behavior tree periodically replans and can invoke spin, backup, drive-on-heading, and wait behaviors.
- **Command path:** Nav2's velocity smoother publishes the final `geometry_msgs/Twist` to `/cmd_vel`, which the existing ros_gz_bridge forwards to Gazebo.

The map was rasterized from the six wall boxes in `worlds/small_maze.sdf`: four perimeter walls and two internal walls. The map uses 0.05 m/cell, 140 x 140 cells, and origin (-3.5, -3.5, 0). If the world geometry changes, regenerate the map to keep it aligned with the simulation.

## 1. Install dependencies (Ubuntu 22.04 / ROS 2 Humble)

```bash
sudo apt update
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-ros-gz-sim \
  ros-humble-ros-gz-bridge \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  python3-colcon-common-extensions \
  python3-rosdep
```

If rosdep has not been initialized on this Ubuntu installation:

```bash
sudo rosdep init
rosdep update
```

## 2. Put the package in a workspace

For example, if the extracted package directory is `sim_mobile_robot`:

```bash
mkdir -p ~/nav_ws/src
cp -r /path/to/sim_mobile_robot ~/nav_ws/src/
cd ~/nav_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

Do not copy the ZIP's old `build/`, `install/`, or `log/` folders into the workspace. They are generated artifacts from another build and are not needed.

## 3. Build and source

```bash
cd ~/nav_ws
colcon build --symlink-install --packages-select sim_mobile_robot
source install/setup.bash
```

To make the overlay available in new terminals:

```bash
echo 'source ~/nav_ws/install/setup.bash' >> ~/.bashrc
```

## 4. Run simulation plus Nav2

```bash
source /opt/ros/humble/setup.bash
source ~/nav_ws/install/setup.bash
ros2 launch sim_mobile_robot navigation.launch.py
```

Wait for Gazebo to finish loading, the robot to spawn, and Nav2 lifecycle nodes to become active. RViz opens with the Nav2 view. The initial AMCL pose is configured as x=0, y=0, yaw=0 because the robot is spawned at the center of this world.

## 5. Check the required topics and transforms

In a second terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/nav_ws/install/setup.bash
ros2 topic list
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

Expected key topics include `/scan`, `/odom`, `/cmd_vel`, `/map`, `/tf`, `/tf_static`, `/amcl_pose`, and Nav2 costmap topics. `tf2_echo` should continuously report transforms. If `/scan` is absent, fix the Gazebo sensor or bridge before starting navigation. If `odom -> base_link` is absent, check the differential-drive plugin and `/tf` bridge.

Check lifecycle state:

```bash
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
```

Each should report `active` after bringup completes.

## 6. Send a navigation goal

Use RViz's **2D Goal Pose** tool: click the desired position and drag to set the final heading. Or send a goal from the terminal:

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
"{pose: {header: {frame_id: map}, pose: {position: {x: 2.2, y: 2.2, z: 0.0}, orientation: {z: 0.0, w: 1.0}}}}"
```

The robot should follow a path around the two internal walls and stop within the configured 0.20 m goal tolerance.

## 7. Test a newly appearing obstacle

Start navigation and send a goal. While the robot is moving, open another terminal and spawn a cylinder into the maze:

```bash
source /opt/ros/humble/setup.bash
source ~/nav_ws/install/setup.bash
ros2 run ros_gz_sim create \
  -world maze_world \
  -file ~/nav_ws/src/sim_mobile_robot/worlds/dynamic_obstacle.sdf \
  -name dynamic_obstacle \
  -x 1.7 -y 1.5 -z 0.25
```

Place the obstacle in the robot's current route but not on top of the robot. The LiDAR should detect it; the costmap obstacle layer should mark it, and DWB should choose a collision-free local trajectory. The global costmap also receives scan obstacles, allowing the behavior tree to replan if the direct route is blocked. Remove the obstacle in Gazebo or reset the simulation after the test.

A newly spawned object is dynamic in the sense that it appears after navigation has begun. The provided cylinder is not animated and does not autonomously drive around the world. A moving actor requires a Gazebo motion system or a separate actor/controller node.

## 8. Useful debugging commands

```bash
ros2 topic echo /scan --once
ros2 topic echo /amcl_pose --once
ros2 topic echo /plan --once
ros2 topic echo /local_costmap/costmap --once
ros2 topic echo /global_costmap/costmap --once
ros2 topic echo /cmd_vel
```

If the robot rotates in place or reports no valid path:

1. Confirm the map matches the SDF wall locations and the robot is inside free map space.
2. Confirm `/scan` has `header.frame_id: laser_frame` and the transform `base_link -> laser_frame` exists.
3. Confirm `odom -> base_link` exists and changes as the robot moves.
4. Confirm AMCL is publishing a pose in the `map` frame.
5. Check the Nav2 logs for footprint collision, transform timeout, or costmap errors.
6. Use RViz to inspect the map, scan, global costmap, local costmap, and planned path.

## 9. Run package tests

```bash
cd ~/nav_ws
source /opt/ros/humble/setup.bash
colcon test --packages-select sim_mobile_robot
colcon test-result --verbose
```

The included tests validate package navigation assets, map metadata, launch wiring, and the robot's LiDAR/odometry frame contract. They do not replace a live Gazebo/Nav2 integration test; the live checks above are required to verify the simulator's actual bridge and TF behavior.

## Configuration notes

- Edit `config/nav2_params.yaml` to tune speed, acceleration, DWB scoring, costmap sizes, and inflation.
- Edit `maps/small_maze.yaml` only when changing map resolution, origin, or image file.
- The map's pixel geometry must remain aligned with `worlds/small_maze.sdf`.
- `navigation.launch.py` accepts `map:=/absolute/path/to/map.yaml`, `params_file:=/absolute/path/to/params.yaml`, and `use_rviz:=false`.
- The original `sim_robot.launch.py` remains available for simulation-only use.
