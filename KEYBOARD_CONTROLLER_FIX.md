# keyboard_controller Node — Vanishing Issue & Fix

## Why Was It Vanishing?
The `keyboard_controller` node was never added to the launch file (`pong.launch.py`). In ROS 2, the launch file is responsible for starting all nodes when you run the game. The original file only listed 2 nodes — `pygame_pong` and `pong_visualizer`. Since `keyboard_controller` was not listed, ROS 2 simply never started it. The node existed in the code but was never told to launch — so it "vanished."

## Where Does It Come From?
The node is defined in `src/pong_game/pong_game/keyboard_controller.py`. It reads keyboard input (W/S for Player 1, Arrow Up/Down for Player 2) and publishes paddle positions to the `/pong/paddle_input` topic. It was registered in `setup.py` under `console_scripts`, meaning it was always available to run — just never told to launch automatically.

## How I Fixed It
Opened `src/pong_game/launch/pong.launch.py` and added this block before the closing `])`:

```python
Node(
    package='pong_game',
    executable='keyboard_controller',
    name='keyboard_controller',
    output='screen'
),
```

Then rebuilt and ran:
```bash
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
ros2 launch pong_game pong.launch.py
```

## How to Verify All 3 Nodes Are Running
Open a second terminal while the game is running:
```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 node list
```

Expected output:
/keyboard_controller

/pong_visualizer

/pygame_pong

To verify they are communicating:
```bash
ros2 topic list
```
You should see `/pong/paddle_input` confirming `keyboard_controller` is publishing and `pygame_pong` is receiving.

## Key Lesson
Just because a node exists in the code and is registered in `setup.py` does NOT mean it will run automatically. Every node must be explicitly listed in the launch file to be started when using `ros2 launch`.
