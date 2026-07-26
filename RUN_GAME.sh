#!/bin/bash
# ROS2 Pong Game - Complete Setup and Run Script
# This script handles environment setup and runs all three nodes

set -e  # Exit on error

echo "========================================"
echo "ROS2 Pong Game - Complete Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Unset any conflicting ROS variables
echo -e "${YELLOW}[1/5] Cleaning ROS environment variables...${NC}"
unset RMW_IMPLEMENTATION
unset AMENT_PREFIX_PATH
unset CMAKE_PREFIX_PATH
unset COLCON_PREFIX_PATH

# Step 2: Source ROS 2 Jazzy
echo -e "${YELLOW}[2/5] Sourcing ROS 2 Jazzy...${NC}"
source /opt/ros/jazzy/setup.bash

# Step 3: Source the workspace
echo -e "${YELLOW}[3/5] Sourcing workspace...${NC}"
source install/setup.bash

# Step 4: Configure ROS network settings
echo -e "${YELLOW}[4/5] Configuring ROS network settings...${NC}"
export ROS_DOMAIN_ID=30
export RMW_FASTRTPS_USE_SHM=0
export RMW_FASTRTPS_USE_SHARED_MEMORY=0
export FASTRTPS_DEFAULT_PROFILES_FILE=~/discovery.xml
export RMW_LOG_LEVEL=FATAL
export DISPLAY=:0

# Step 5: Build if needed
echo -e "${YELLOW}[5/5] Checking if build is needed...${NC}"
if [ ! -d "install" ]; then
    echo -e "${YELLOW}Building project...${NC}"
    colcon build
fi

# Summary
echo -e "${GREEN}========================================"
echo "Setup Complete! Ready to run nodes"
echo "========================================${NC}"
echo ""
echo "To run the game, use these commands in separate terminals:"
echo ""
echo -e "${GREEN}Terminal 1 - Game Main Node:${NC}"
echo "  cd $(pwd)"
echo "  source /opt/ros/jazzy/setup.bash && source install/setup.bash"
echo "  export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0"
echo "  ros2 run pong_game pygame_pong"
echo ""
echo -e "${GREEN}Terminal 2 - Keyboard Controller:${NC}"
echo "  cd $(pwd)"
echo "  source /opt/ros/jazzy/setup.bash && source install/setup.bash"
echo "  export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0"
echo "  ros2 run pong_game keyboard_controller"
echo ""
echo -e "${GREEN}Terminal 3 - Visualizer (rviz2):${NC}"
echo "  cd $(pwd)"
echo "  source /opt/ros/jazzy/setup.bash && source install/setup.bash"
echo "  export ROS_DOMAIN_ID=30 RMW_FASTRTPS_USE_SHM=0"
echo "  ros2 run pong_game visualizer"
echo ""
echo -e "${YELLOW}To verify all nodes are running:${NC}"
echo "  ros2 node list"
echo ""
echo -e "${YELLOW}To verify all topics are publishing:${NC}"
echo "  ros2 topic list"
echo ""
echo -e "${YELLOW}To monitor game state messages:${NC}"
echo "  ros2 topic echo /pong/game_state"
echo ""
