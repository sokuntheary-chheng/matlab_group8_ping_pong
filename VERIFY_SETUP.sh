#!/bin/bash
# ROS2 Pong Game - Verification and Troubleshooting Script
# Use this to verify all nodes and topics are running correctly

set -e

echo "========================================"
echo "ROS2 Pong Game - Verification Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configure environment
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=30
export RMW_FASTRTPS_USE_SHM=0
export RMW_FASTRTPS_USE_SHARED_MEMORY=0
export RMW_LOG_LEVEL=FATAL

echo -e "${BLUE}1. Checking ROS 2 Installation${NC}"
echo "======================================"
if ros2 --version &>/dev/null; then
    echo -e "${GREEN}✓ ROS 2 is installed${NC}"
    ros2 --version
else
    echo -e "${RED}✗ ROS 2 not found${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}2. Checking Python Packages${NC}"
echo "======================================"
python3 -c "import rclpy; print('✓ rclpy OK')" 2>/dev/null || echo -e "${RED}✗ rclpy not found${NC}"
python3 -c "import pygame; print('✓ pygame OK')" 2>/dev/null || echo -e "${RED}✗ pygame not found${NC}"
python3 -c "import numpy; print('✓ numpy OK')" 2>/dev/null || echo -e "${RED}✗ numpy not found${NC}"
echo ""

echo -e "${BLUE}3. Checking Custom Message Types${NC}"
echo "======================================"
if ros2 msg list | grep -q "pong_msgs"; then
    echo -e "${GREEN}✓ pong_msgs package found${NC}"
    ros2 msg list | grep pong_msgs
else
    echo -e "${RED}✗ pong_msgs not found - rebuilding...${NC}"
    colcon build --packages-select pong_msgs
    colcon build --packages-select pong_game
fi
echo ""

echo -e "${BLUE}4. Checking ROS 2 Executables${NC}"
echo "======================================"
echo "Available Pong Game executables:"
for exe in pygame_pong keyboard_controller visualizer pong_client game_logic; do
    if ros2 pkg executables pong_game | grep -q $exe; then
        echo -e "${GREEN}  ✓ $exe${NC}"
    else
        echo -e "${RED}  ✗ $exe${NC}"
    fi
done
echo ""

echo -e "${BLUE}5. Network Configuration${NC}"
echo "======================================"
echo "ROS_DOMAIN_ID: ${ROS_DOMAIN_ID}"
echo "RMW_FASTRTPS_USE_SHM: ${RMW_FASTRTPS_USE_SHM}"
echo "RMW_FASTRTPS_USE_SHARED_MEMORY: ${RMW_FASTRTPS_USE_SHARED_MEMORY}"
echo ""

echo -e "${BLUE}6. Checking Running Nodes (if any)${NC}"
echo "======================================"
echo "Active nodes:"
ros2 node list 2>/dev/null || echo -e "${YELLOW}No nodes running${NC}"
echo ""

echo -e "${BLUE}7. Checking Active Topics (if any)${NC}"
echo "======================================"
echo "Active topics:"
ros2 topic list 2>/dev/null || echo -e "${YELLOW}No topics active${NC}"
echo ""

echo -e "${GREEN}========================================"
echo "Verification Complete!"
echo "========================================${NC}"
echo ""
echo -e "${YELLOW}TROUBLESHOOTING TIPS:${NC}"
echo "1. If pygame_pong doesn't display:"
echo "   - Check DISPLAY variable: echo \$DISPLAY (should be :0 or :1)"
echo "   - Try: export DISPLAY=:0"
echo "   - For WSL, you may need VcXsrv or Windows 11 WSLg"
echo ""
echo "2. If nodes don't communicate:"
echo "   - Verify all nodes are started in separate terminals"
echo "   - Check: ros2 topic hz /pong/game_state (should be ~20Hz)"
echo "   - Try: ros2 topic echo /pong/game_state"
echo ""
echo "3. If keyboard_controller doesn't work:"
echo "   - Make sure it's running in a terminal with input"
echo "   - Try pressing: w, s, q (for Player 1 paddle or quit)"
echo "   - Arrow Up/Down for Player 2"
echo ""
echo "4. If visualizer crashes:"
echo "   - Make sure pygame_pong is running first"
echo "   - Wait for game to start (game state will publish)"
echo "   - Then launch rviz2 and add MarkerArray display"
echo ""
echo -e "${YELLOW}QUICK TEST SEQUENCE:${NC}"
echo "1. Terminal 1: ros2 run pong_game pygame_pong"
echo "2. Wait 2 seconds for game to initialize"
echo "3. Terminal 2: ros2 run pong_game keyboard_controller"
echo "4. Terminal 3: ros2 run pong_game visualizer"
echo "5. Terminal 4 (check): ros2 node list"
echo "6. Terminal 4 (check): ros2 topic list"
echo "7. Terminal 4 (check): ros2 topic hz /pong/game_state"
echo ""
