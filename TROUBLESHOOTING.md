# ROS2 Pong Game - Complete Troubleshooting Guide

## Issue Summary & Solutions

### ❌ **Game Window Doesn't Appear**

**Causes:**
1. DISPLAY environment variable not set or incorrect
2. No X server running (WSL2 without WSLg or VcXsrv)
3. pygame initialization failure

**Solutions:**

```bash
# Check DISPLAY
echo $DISPLAY  # Should show :0, :1, or similar (not empty)

# If empty, try:
export DISPLAY=:0

# For WSL2 Users:
# Option 1: Use Windows 11 WSLg (built-in, no additional setup)
# Option 2: Install VcXsrv
#   - Download from: https://sourceforge.net/projects/vcxsrv/
#   - Run: vcxsrv.exe
#   - In WSL: export DISPLAY=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}'):0

# Test display:
echo "test" | xmessage -file -  # Should show a message box
```

---

### ❌ **Visualizer Node Crashes or Doesn't Receive Data**

**Cause:**
- Visualizer starts before pygame_pong publishes to /pong/game_state
- ROS2 network communication hasn't established

**Solution:**

```bash
# Terminal 1: Start pygame_pong FIRST
ros2 run pong_game pygame_pong

# Wait 3-5 seconds for game to initialize and start publishing

# Terminal 2: Then start visualizer
ros2 run pong_game visualizer

# Terminal 3: Verify data flow
ros2 topic hz /pong/game_state  # Should show ~20 Hz
ros2 topic echo /pong/game_state | head -5  # Should show game state data
```

---

### ❌ **Keyboard Controller Not Responding**

**Causes:**
1. Terminal is not active/focused
2. Input is not going to the right process
3. Terminal doesn't support raw mode

**Solutions:**

```bash
# Make sure you're running it in an INTERACTIVE terminal:
ros2 run pong_game keyboard_controller

# Keep this terminal FOCUSED (click in it before typing)
# Then try:
# - w = Player 1 up
# - s = Player 1 down  
# - Arrow Up = Player 2 up
# - Arrow Down = Player 2 down
# - q = quit

# If it still doesn't work:
# Option 1: Run from WSL terminal (not Windows Terminal if possible)
# Option 2: Use pygame_pong as Player 1, keyboard_controller as Player 2
# Option 3: Check logs for errors:
ros2 run pong_game keyboard_controller | grep -i error

# Verify messages are being published:
ros2 topic echo /pong/paddle_input
```

---

### ❌ **Nodes Don't Communicate / No Topics Appear**

**Causes:**
1. ROS_DOMAIN_ID mismatch
2. Middleware configuration issues
3. Firewall blocking communication

**Solutions:**

```bash
# 1. Verify ROS_DOMAIN_ID is set on ALL terminals:
echo $ROS_DOMAIN_ID  # Should be 30

# If not set, run:
export ROS_DOMAIN_ID=30

# 2. Configure middleware on ALL terminals:
export RMW_FASTRTPS_USE_SHM=0
export RMW_FASTRTPS_USE_SHARED_MEMORY=0
export RMW_LOG_LEVEL=FATAL

# 3. Source ROS on ALL terminals:
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash  # or wherever you installed

# 4. Then start nodes and verify:
ros2 node list
ros2 topic list
```

---

### ❌ **"Build Fails — pong_msgs not found"**

**Solution:**

```bash
cd ~/ros2_ws  # or your workspace root

# Option 1: Full rebuild
colcon build

# Option 2: Selective rebuild
colcon build --packages-select pong_msgs
source install/setup.bash
colcon build --packages-select pong_game
source install/setup.bash

# Verify messages are available:
ros2 msg list | grep pong_msgs
```

---

### ❌ **"pygame AVX2 Warning"**

**This is just a warning, NOT an error.**
```
RuntimeWarning: Your system is avx2 capable but pygame was not built with support for it
```

The game runs fine. You can suppress it:
```bash
export PYGAME_DETECT_AVX2=1
export PYGAME_HIDE_SUPPORT_PROMPT=1
```

---

### ❌ **Network Mode: Guest Paddle Not Responding**

**Causes:**
1. HOST and CLIENT not on same WiFi
2. ROS_DOMAIN_ID mismatch
3. Firewall blocking UDP ports
4. Heartbeat threshold not reached

**Solutions:**

```bash
# On BOTH PCs:
export ROS_DOMAIN_ID=0  # Default domain for network play

# Verify both PCs can see each other:
ping <partner_ip>  # Should get responses

# Terminal 1 (HOST PC):
ros2 run pong_game pygame_pong
# → Select "Across 2 PCs" → Click "Start as HOST"

# Terminal 1 (GUEST PC):
ros2 run pong_game pong_client
# → Select "Join as CLIENT" → Enter HOST IP → Click "Connect"

# Verify connection:
# Look for "Heartbeat 1/3", "Heartbeat 2/3", "Heartbeat 3/3" in logs

# If still not working:
# - Check on-screen debug overlay shows correct ROLE and last-seen timestamps
# - Verify firewall isn't blocking ROS 2 traffic
# - Try setting: export RMW_FASTRTPS_USE_SHM=0 on both PCs
```

---

### ❌ **WSL2 Specific: "Failed init_port fastrtps_port7005"**

**Cause:**
- Fast DDS shared-memory transport port conflicts (common in WSL2)

**Solution (already configured in our code):**
```bash
# These are already set in the node code, but ensure they're in your environment:
export RMW_FASTRTPS_USE_SHM=0
export RMW_FASTRTPS_USE_SHARED_MEMORY=0

# This error is benign — communication falls back to UDP
# The game should still work fine
```

---

## Verification Checklist

Before reporting issues, verify:

- [ ] ROS 2 Jazzy is installed: `ros2 --version`
- [ ] Custom messages are built: `ros2 msg list | grep pong_msgs`
- [ ] All executables exist: `ros2 pkg executables pong_game`
- [ ] pygame_pong starts first
- [ ] Wait 3-5 seconds before starting visualizer
- [ ] All three terminals have: `source /opt/ros/jazzy/setup.bash && source install/setup.bash`
- [ ] All three terminals have: `export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0`
- [ ] Topics appear: `ros2 topic list` (should show /pong/* topics)
- [ ] Game publishes data: `ros2 topic hz /pong/game_state` (should show ~20 Hz)

---

## Quick Test Sequence

```bash
# Terminal 1 — Game Engine
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL DISPLAY=:0
ros2 run pong_game pygame_pong

# Wait 3-5 seconds...

# Terminal 2 — Keyboard Input
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL
ros2 run pong_game keyboard_controller

# Terminal 3 — rviz2 Visualization
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0 RMW_LOG_LEVEL=FATAL
ros2 run pong_game visualizer

# Terminal 4 — Verify (optional but recommended)
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0
ros2 node list    # Should show /pygame_pong, /keyboard_controller, /pong_visualizer
ros2 topic list   # Should show /pong/game_state, /pong/paddle_input, /pong/score_event, /pong/markers
ros2 topic hz /pong/game_state  # Should show ~20 Hz
```

---

## Debug Commands Reference

```bash
# List all nodes
ros2 node list

# List all topics
ros2 topic list

# List all services
ros2 service list

# Show message rate
ros2 topic hz /pong/game_state

# View raw messages
ros2 topic echo /pong/game_state

# View node info
ros2 node info /pygame_pong

# View topic info
ros2 topic info /pong/game_state

# View message type
ros2 topic type /pong/game_state

# Inspect message definition
ros2 interface show pong_msgs/msg/PongGameState
```

---

## Performance Expectations

| Metric | Expected Value |
|---|---|
| Game Update Rate | 20 Hz |
| Render Rate | 60 FPS |
| Topic Latency | < 50ms |
| Visualizer Display Lag | < 100ms after game event |
| Keyboard Response | < 50ms |

If you're seeing significantly worse performance, check:
1. CPU usage: `htop` (should be < 80% per core)
2. Memory usage: `free -h` (should have > 1GB free)
3. Network latency: `ping localhost` (should be < 1ms)

---

## Still Having Issues?

1. Run the verification script: `bash VERIFY_SETUP.sh`
2. Check the [GitHub Issues](https://github.com/sokuntheary-chheng/matlab_group8_ping_pong/issues)
3. Collect logs from all three terminals and share them
4. Include: OS version, ROS version, Python version, pygame version

