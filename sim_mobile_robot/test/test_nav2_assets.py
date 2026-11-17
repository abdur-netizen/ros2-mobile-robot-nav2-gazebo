from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def test_navigation_configuration_contains_dynamic_lidar_costmaps():
    config = (PACKAGE_ROOT / 'config' / 'nav2_params.yaml').read_text()
    assert 'nav2_navfn_planner/NavfnPlanner' in config
    assert 'dwb_core::DWBLocalPlanner' in config
    assert 'nav2_costmap_2d::ObstacleLayer' in config
    assert 'topic: /scan' in config
    assert 'clearing: true' in config
    assert 'plugin_lib_names:' in config
    assert 'navigators:' not in config
    assert '[[0.30, 0.25]' in config
    assert 'marking: true' in config


def test_static_map_matches_maze_dimensions_and_origin():
    map_yaml = (PACKAGE_ROOT / 'maps' / 'small_maze.yaml').read_text()
    pgm = (PACKAGE_ROOT / 'maps' / 'small_maze.pgm').read_text().split()
    assert 'resolution: 0.05' in map_yaml
    assert 'origin: [-3.5, -3.5, 0.0]' in map_yaml
    assert pgm[0] == 'P2'
    assert pgm[1:4] == ['140', '140', '255']


def test_navigation_launch_uses_localization_and_navigation_launch_files():
    launch = (PACKAGE_ROOT / 'launch' / 'navigation.launch.py').read_text()
    assert 'localization_launch.py' in launch
    assert 'navigation_launch.py' in launch
    assert 'small_maze.yaml' in launch


def test_robot_description_has_lidar_frame_and_diff_drive_odom():
    urdf = (PACKAGE_ROOT / 'urdf' / 'sim_robot_org.urdf').read_text()
    assert 'name="laser_frame"' in urdf
    assert '<child_frame_id>base_link</child_frame_id>' in urdf
    assert '<odom_topic>/odom</odom_topic>' in urdf


def test_launch_files_are_valid_python():
    import ast

    for launch_file in (PACKAGE_ROOT / 'launch').glob('*.launch.py'):
        ast.parse(launch_file.read_text())


def test_dynamic_obstacle_model_is_non_static_and_has_collision():
    obstacle = (PACKAGE_ROOT / 'worlds' / 'dynamic_obstacle.sdf').read_text()
    assert '<static>false</static>' in obstacle
    assert '<collision name="collision">' in obstacle


def test_map_marks_start_and_sample_goal_free_and_inner_wall_occupied():
    tokens = (PACKAGE_ROOT / 'maps' / 'small_maze.pgm').read_text().split()
    width, height = int(tokens[1]), int(tokens[2])
    pixels = [int(value) for value in tokens[4:]]

    def pixel_at_world(x, y):
        resolution = 0.05
        origin_x = -3.5
        origin_y = -3.5
        column = int((x - origin_x) / resolution)
        row_from_bottom = int((y - origin_y) / resolution)
        row = height - 1 - row_from_bottom
        return pixels[row * width + column]

    assert pixel_at_world(0.0, 0.0) == 254
    assert pixel_at_world(2.2, 2.2) == 254
    assert pixel_at_world(-1.0, 1.0) == 0


def test_global_costmap_also_tracks_new_lidar_obstacles():
    config = (PACKAGE_ROOT / 'config' / 'nav2_params.yaml').read_text()
    global_costmap = config.split('global_costmap:', 1)[1]
    assert 'nav2_costmap_2d::ObstacleLayer' in global_costmap
    assert 'topic: /scan' in global_costmap
    assert 'marking: true' in global_costmap
    assert 'clearing: true' in global_costmap
