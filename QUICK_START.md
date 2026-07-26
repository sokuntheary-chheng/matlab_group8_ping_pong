# 🚀 ROS2 Pong Game - Quick Start Guide

## What Was Fixed

Your game had several critical issues that have now been resolved:

| Issue | Status | Fix |
|---|---|---|
| Game window not displaying | ✅ FIXED | Added DISPLAY environment setup and validation |
| Keyboard controller crashes | ✅ FIXED | Improved error handling and terminal detection |
| Visualizer waiting for data | ✅ FIXED | Now publishes initial markers and waits gracefully |
| Incomplete message publishing | ✅ FIXED | All message fields now properly populated |
| No clear setup instructions | ✅ FIXED | Added RUN_GAME.sh and VERIFY_SETUP.sh scripts |
| Hard to debug issues | ✅ FIXED | Created comprehensive TROUBLESHOOTING.md guide |

---

## The 3 Nodes You Need

### 1️⃣ **pygame_pong** (Main Game Engine)
- **What it does**: Runs the pygame window, handles game physics, publishes game state
- **Publishes**: `/pong/game_state` (20 Hz), `/pong/score_event`
- **Subscribes**: `/pong/paddle_input` (for keyboard/network control)
- **Command**: `ros2 run pong_game pygame_pong`

### 2️⃣ **keyboard_controller** (Input Handler)
- **What it does**: Reads keyboard input, sends paddle positions
- **Publishes**: `/pong/paddle_input` (20 Hz)
- **Keys**: W/S for Player 1, Arrow Up/Down for Player 2
- **Command**: `ros2 run pong_game keyboard_controller`

### 3️⃣ **visualizer** (rviz2 Visualization)
- **What it does**: Subscribes to game state, publishes markers for rviz2
- **Publishes**: `/pong/markers` (20 Hz)
- **Subscribes**: `/pong/game_state`
- **Command**: `ros2 run pong_game visualizer`

---

## The 4 Topics

```
pygame_pong → /pong/game_state → visualizer
         ↓
  (listens to)
         ↓
/pong/paddle_input ← keyboard_controller

pygame_pong → /pong/score_event → (logged to terminal)

visualizer → /pong/markers → rviz2
```

---

## 🎮 Run the Game (Recommended Order)

**Open 4 terminals in your WSL2 or Ubuntu environment:**

### Terminal 1: Setup Environment
```bash
cd ~/ros2_ws  # or wherever you cloned the repo
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30
export RMW_FASTRTPS_USE_SHM=0
export RMW_FASTRTPS_USE_SHARED_MEMORY=0
export RMW_LOG_LEVEL=FATAL
export DISPLAY=:0
```

### Terminal 2: Start pygame_pong (FIRST - do this first!)
```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL DISPLAY=:0
ros2 run pong_game pygame_pong
```
✅ **Wait 3-5 seconds** for the game window to appear and initialize

### Terminal 3: Start keyboard_controller
```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL
ros2 run pong_game keyboard_controller
```
ℹ️ You should see: `Keyboard Controller started!`

### Terminal 4: Start visualizer
```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL
ros2 run pong_game visualizer
```
ℹ️ You should see: `Pong Visualizer started!` then `Received first game state!`

### (Optional) Terminal 5: Verify Everything Works
```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL

# Check all nodes are running
echo "=== Running Nodes ==="
ros2 node list

# Check all topics are active
echo -e "\n=== Active Topics ==="
ros2 topic list

# Check game state publishing rate
echo -e "\n=== Game State Publishing Rate ==="
ros2 topic hz /pong/game_state

# Monitor live messages
echo -e "\n=== Live Game State ==="
ros2 topic echo /pong/game_state | head -5
```

---

## 🐛 Common Issues & Quick Fixes

### ❌ "Game window doesn't appear"
**Solution:**
```bash
export DISPLAY=:0  # Or :1, :2 depending on your X server
echo $DISPLAY      # Should NOT be empty
```

### ❌ "Nodes don't see each other"
**Solution:** Make sure ALL terminals have these set:
```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30
export RMW_FASTRTPS_USE_SHM=0
```

### ❌ "Keyboard input not working"
**Solution:** Click on the keyboard_controller terminal to focus it, then try:
- `w` = Player 1 up
- `s` = Player 1 down
- Arrow Up = Player 2 up
- Arrow Down = Player 2 down

### ❌ "Visualizer won't start"
**Solution:** Make sure pygame_pong is running first. Wait 3-5 seconds before starting visualizer.

For more issues, see **TROUBLESHOOTING.md**

---

## 📊 Verify With These Commands

```bash
# Show running nodes (should have 3):
ros2 node list
# Expected output:
# /pygame_pong
# /keyboard_controller
# /pong_visualizer

# Show active topics (should have 4+):
ros2 topic list
# Expected output:
# /parameter_events
# /pong/game_state
# /pong/markers
# /pong/paddle_input
# /pong/score_event
# /rosout

# Show publishing rate of game state (should be ~20 Hz):
ros2 topic hz /pong/game_state
# Expected: average rate: 20.00

# See raw game state messages:
ros2 topic echo /pong/game_state
# Should show ball position, paddle positions, scores updating
```

---

## 📂 File Structure Reference

```
.
├── src/pong_game/pong_game/
│   ├── pygame_pong.py          ← Main game node (run this FIRST)
│   ├── keyboard_controller.py   ← Input node (run this SECOND)
│   ├── visualizer.py           ← rviz2 node (run this THIRD)
│   ├── pong_client.py          ← Network client for 2-PC mode
│   ├── game_logic.py           ← Shared game physics
│   ├── sound_gen.py            ← Audio generation
│   ├── settings.py             ← Game settings
│   └── network_controls.py     ← Network helpers
├── src/pong_msgs/              ← Custom ROS2 messages
├── RUN_GAME.sh                 ← Setup script (NEW)
├── VERIFY_SETUP.sh             ← Verification script (NEW)
└── TROUBLESHOOTING.md          ← This troubleshooting guide (NEW)
```

---

## 🔧 Build Instructions (If Needed)

```bash
cd ~/ros2_ws
colcon build --packages-select pong_msgs
colcon build --packages-select pong_game
source install/setup.bash
```

---

## 🎯 Next Steps

1. ✅ Follow the "Run the Game" section above
2. ✅ Open Terminal 2 and start pygame_pong
3. ✅ Wait 3-5 seconds
4. ✅ Open Terminals 3 & 4 to start keyboard_controller and visualizer
5. ✅ Use Terminal 5 to verify everything is running
6. ✅ Play the game! (See README.md for game controls)

---

## 📚 Learn More

- **Full game guide**: See README.md for detailed game modes, controls, settings
- **Troubleshooting**: See TROUBLESHOOTING.md for detailed issue solutions
- **Verification**: See VERIFY_SETUP.sh for automated environment checking
- **Network mode**: See README.md "How to Play → Network Mode" section

---

## 🆘 Still Having Issues?

1. Run the verification script:
   ```bash
   bash VERIFY_SETUP.sh
   ```

2. Check the comprehensive troubleshooting guide:
   ```bash
   cat TROUBLESHOOTING.md
   ```

3. Collect output from all three terminals and review for error messages

4. Check that all 4 topics are active:
   ```bash
   ros2 topic list | grep /pong/
   ```

---

**Made with ❤️ using ROS 2 Jazzy + pygame**

Group 8 - ITC
