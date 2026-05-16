# 🏓 ROS 2 Pong Game

<div align="center">

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue?style=for-the-badge&logo=ros)
![Python](https://img.shields.io/badge/Python-3.12-yellow?style=for-the-badge&logo=python)
![pygame](https://img.shields.io/badge/pygame-2.5.2-green?style=for-the-badge)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-orange?style=for-the-badge&logo=ubuntu)
![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)

**A fully playable Pong game built with ROS 2 Jazzy and pygame**
**featuring custom messages, AI opponent, multiplayer, and MATLAB integration**

*ITC Year 2 | Semester 2 | Group 8*

</div>

---

## 📖 Table of Contents
- [About](#-about)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Custom Messages](#-custom-messages)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [How to Play](#-how-to-play)
- [MATLAB Integration](#-matlab-integration)
- [Project Structure](#-project-structure)
- [Team](#-team)

---

## 🎮 About

This project is a **mini project for Seminar and Project IV** course at ITC.
We built a classic Pong game using **ROS 2 Jazzy** middleware to demonstrate
real-time communication between nodes using **custom message types**.

The game features:
- A beautiful **pygame GUI** with particle effects and background music
- **3 game modes** including AI, local multiplayer, and network multiplayer
- **Custom ROS 2 messages** for game state and score events
- **MATLAB integration** for real-time data visualization
- **rviz2 visualization** with MarkerArray

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 vs AI | Play against an AI opponent that gets harder as speed increases |
| 👥 2 Players | Two players on the same PC using different keys |
| 🌐 Network | Play across two PCs on the same WiFi network |
| 🎵 Background Music | Retro chiptune music generated programmatically |
| 🔊 Sound Effects | Paddle hit, wall bounce, score, and win sounds |
| ✨ Particle Effects | Visual particles on paddle hit and scoring |
| 🏠 Home Screen | Beautiful menu with animated background particles |
| 📊 MATLAB Integration | Real-time game data visualization in MATLAB |
| 📡 rviz2 | ROS 2 visualization with MarkerArray |
| 🏆 Score System | Custom PongScore message for score events |
| ⚡ Speed Increase | Ball speeds up with each paddle hit |

---

## 🏗 System Architecture
┌─────────────────────────────────────────────────────────┐
│                    ROS 2 Pong System                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    /pong/paddle_input              │
│  │keyboard_controller│──────────────────────┐           │
│  └──────────────────┘                       ▼           │
│                                   ┌─────────────────┐   │
│                                   │   pygame_pong   │   │
│                                   │  (Main Node)    │   │
│                                   └────────┬────────┘   │
│                                            │            │
│              ┌─────────────────────────────┤            │
│              │                             │            │
│              ▼ /pong/game_state            ▼            │
│   ┌──────────────────┐        /pong/score_event         │
│   │    visualizer    │                    │             │
│   │   (rviz2 markers)│        ┌───────────▼──────────┐  │
│   └──────────────────┘        │   MATLAB Subscriber  │  │
│                                │  (Real-time plots)  │  │
│                                └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘

### ROS 2 Topics

| Topic | Message Type | Description |
|---|---|---|
| `/pong/game_state` | `pong_msgs/PongGameState` | Ball position, velocity, scores |
| `/pong/paddle_input` | `pong_msgs/PongGameState` | Paddle position input |
| `/pong/score_event` | `pong_msgs/PongScore` | Score and win events |
| `/pong/markers` | `visualization_msgs/MarkerArray` | rviz2 visualization |

---

## 📨 Custom Messages

### PongGameState.msg
Ball state
float32 ball_x          # Ball X position (pixels)
float32 ball_y          # Ball Y position (pixels)
float32 ball_vel_x      # Ball X velocity
float32 ball_vel_y      # Ball Y velocity
Paddle positions
float32 paddle1_y       # Player 1 paddle Y position
float32 paddle2_y       # Player 2 paddle Y position
Score
int32 score_player1     # Player 1 score
int32 score_player2     # Player 2 score
Game status
int32 game_status       # 0=waiting 1=playing 2=p1wins 3=p2wins

### PongScore.msg
int32 player_scored     # 1=player1, 2=player2
int32 score_player1     # Current score player 1
int32 score_player2     # Current score player 2
string event_type       # "score", "win", "start", "reset"
string winner           # "player1", "player2", "ai", ""

---

## 💻 Requirements

### System
- Windows 10/11 with WSL2
- Ubuntu 24.04 LTS
- At least 10GB free disk space
- Internet connection for installation

### Software
- ROS 2 Jazzy
- Python 3.12
- pygame 2.5.2
- numpy
- Git

---

## 🚀 Installation

### Step 1: Install WSL2 (Windows)
Open PowerShell as Administrator:
```powershell
wsl --install -d Ubuntu-24.04
```
Restart your computer when prompted.

### Step 2: Open Ubuntu and fix DNS
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Step 3: Fix Ubuntu sources
```bash
sudo tee /etc/apt/sources.list << 'SOURCES'
deb http://archive.ubuntu.com/ubuntu noble main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu noble-security main restricted universe multiverse
SOURCES
sudo apt update
```

### Step 4: Install ROS 2 Jazzy
```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu noble main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-jazzy-desktop
sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-pip
```

### Step 5: Setup ROS 2 environment
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 6: Install pygame and numpy
```bash
sudo apt install -y python3-pygame python3-numpy
```

### Step 7: Clone and build
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/sokuntheary-chheng/matlab_group8_ping_pong.git .
cd ~/ros2_ws
colcon build
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 8: Run the game! 🎮
```bash
ros2 run pong_game pygame_pong
```

---

## 🎮 How to Play

### Single Player (vs AI)
1. Select **"vs AI"** from the home screen
2. Controls:
   - **W** → Move paddle up
   - **S** → Move paddle down
3. First to **5 points** wins!
4. Ball speeds up with every paddle hit!

### Two Players (Same PC)
1. Select **"2 Players"** from the home screen
2. Controls:

| Player | Up | Down |
|---|---|---|
| Player 1 (Left) | W | S |
| Player 2 (Right) | ↑ | ↓ |

3. First to **5 points** wins!

### Network Mode (2 PCs)
1. Both PCs must be on the **same WiFi/Hotspot**
2. **PC 1 (Host):** Select **"Network"** → Press **SPACE**
3. **PC 2 (Client):**
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run pong_game keyboard_controller
```

### General Controls
| Key | Action |
|---|---|
| ESC | Back to home screen |
| R | Restart game |
| Q | Quit keyboard controller |

---

## 📊 MATLAB Integration

### Requirements
- MATLAB R2024b
- ROS Toolbox
- Python 3.10 configured in ROS Toolbox preferences
- Visual Studio Build Tools 2022

### Setup Custom Messages in MATLAB
```matlab
% Generate custom messages
folderPath = 'path/to/pong_msgs';
ros2genmsg(folderPath)
```

### Subscribe to Game State
```matlab
% Create ROS 2 node and subscriber
node = ros2node("/matlab_pong_monitor");
sub_state = ros2subscriber(node, "/pong/game_state", ...
            "pong_msgs/PongGameState");
sub_score = ros2subscriber(node, "/pong/score_event", ...
            "pong_msgs/PongScore");

% Real-time visualization
figure('Name', 'ROS 2 Pong Monitor', 'NumberTitle', 'off');

while true
    % Get latest game state
    msg = receive(sub_state, 10);
    
    % Plot ball position
    subplot(2, 2, 1);
    plot(msg.BallX, msg.BallY, 'co', 'MarkerSize', 15, ...
         'MarkerFaceColor', 'cyan');
    xlim([0 900]); ylim([0 600]);
    title('Ball Position');
    xlabel('X'); ylabel('Y');
    grid on;
    
    % Plot scores
    subplot(2, 2, 2);
    bar([msg.ScorePlayer1, msg.ScorePlayer2], ...
        'FaceColor', 'flat', ...
        'CData', [0 1 0; 1 0 0]);
    set(gca, 'XTickLabel', {'Player 1', 'Player 2'});
    ylim([0 5]);
    title('Score');
    grid on;
    
    % Plot ball velocity
    subplot(2, 2, 3);
    quiver(0, 0, msg.BallVelX, msg.BallVelY, 'b', 'LineWidth', 2);
    xlim([-15 15]); ylim([-15 15]);
    title('Ball Velocity Vector');
    grid on;
    
    % Plot paddle positions
    subplot(2, 2, 4);
    bar([msg.Paddle1Y, msg.Paddle2Y]);
    set(gca, 'XTickLabel', {'Paddle 1', 'Paddle 2'});
    ylim([0 600]);
    title('Paddle Positions');
    grid on;
    
    drawnow;
end
```

---

## 📁 Project Structure
ros2_ws/
└── src/
├── pong_msgs/                    # Custom message package
│   ├── msg/
│   │   ├── PongGameState.msg    # Main game state message
│   │   └── PongScore.msg        # Score event message
│   ├── CMakeLists.txt
│   └── package.xml
│
└── pong_game/                    # Game package
├── pong_game/
│   ├── init.py
│   ├── pygame_pong.py        # Main game + GUI + ROS2 node
│   ├── sound_gen.py          # Sound effects + BGM generator
│   ├── game_logic.py         # Ball physics node
│   ├── keyboard_controller.py # Network keyboard input
│   └── visualizer.py         # rviz2 MarkerArray publisher
├── launch/
│   └── pong.launch.py        # Launch all nodes
├── resource/
├── test/
├── package.xml
├── setup.py
└── setup.cfg

---

## 🔧 Troubleshooting

### WSL2 network issues
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### ROS 2 not found
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

### pygame AVX2 warning
This is just a warning, not an error. The game still runs fine.

### MATLAB can't find Python
1. Open MATLAB → Home → Preferences → ROS Toolbox
2. Set Python path to:
   `C:\Users\<username>\AppData\Local\Programs\Python\Python310\python.exe`
3. Click "Recreate Python Environment"

---

## 👥 Team

| Name | Role |
|---|---|
| Sokuntheary Chheng | Team Lead, Architecture, MATLAB Integration |
| Member 2 | Game Logic, Physics |
| Member 3 | Visualization, Keyboard Controller |

**Course:** Seminar and Project IV
**Institution:** Institute of Technology of Cambodia (ITC)
**Year:** 2 | **Semester:** 2 | **Group:** 8

---

<div align="center">
Made with ❤️ using ROS 2 Jazzy + pygame
</div>
EOF
