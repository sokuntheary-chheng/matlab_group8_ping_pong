# 🏓 ROS 2 Pong Game

<div align="center">

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue?style=for-the-badge&logo=ros)
![Python](https://img.shields.io/badge/Python-3.12-yellow?style=for-the-badge&logo=python)
![pygame](https://img.shields.io/badge/pygame-2.5.2-green?style=for-the-badge)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-orange?style=for-the-badge&logo=ubuntu)
![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)

**A fully playable Pong game built with ROS 2 Jazzy and pygame**
**featuring custom messages, AI opponent, local multiplayer, and network multiplayer**

*Institute of Technology of Cambodia (ITC)*
*Course: Seminar and Project IV | Lecturer: Dr. SRANG Sarot*
*Year 2 | Semester 2 | Group 8*

</div>

---

## 👥 Team Members

| Name | Student ID |
|---|---|
| Chheng Sokuntheary | p20240044 |
| Nhem Phada | p20240058 |
| Dara Panhaseth | p20250002 |

---

## 📖 Table of Contents
- [About](#-about)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Custom Messages](#-custom-messages)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [How to Play](#-how-to-play)
- [Settings](#-settings)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎮 About

This project is a **mini project for Seminar and Project IV** course at ITC.
We built a classic Pong game using **ROS 2 Jazzy** middleware to demonstrate
real-time communication between nodes using **custom message types**.

The game showcases:
- A **pygame GUI** with particle effects, ball trail, and background music
- **3 game modes**: vs AI, local 2 players, and network multiplayer across 2 PCs
- **2 custom ROS 2 message types**: `PongGameState` and `PongScore`
- **3 ROS 2 nodes** communicating via **4 topics** in real time
- **rviz2 MarkerArray** visualization synchronized with gameplay
- A full **settings dashboard** with persistent JSON storage

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 vs AI | Play against an AI opponent with Easy / Normal / Hard difficulty |
| 👥 2 Players | Two players on the same PC using different keys |
| 🌐 Network | Play across two PCs on the same WiFi — Guest sees full game display |
| 🎵 Background Music | Retro chiptune music generated programmatically using NumPy |
| 🔊 Sound Effects | Paddle hit, wall bounce, score, and win sounds |
| ✨ Particle Effects | Visual particles on paddle hit and scoring |
| 🏠 Home Screen | Animated menu with floating particles |
| ⚙️ Settings Dashboard | 5-tab settings panel: Gameplay, Audio, Display, Controls, Accessibility |
| 📡 rviz2 | Real-time MarkerArray visualization of ball, paddles, and walls |
| 🏆 Score System | Custom PongScore message for score and win events |
| ⚡ Speed Increase | Ball speeds up by configurable % with each paddle hit |
| 🎨 Accessibility | Colorblind mode and high contrast mode |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ROS 2 Pong System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────┐   /pong/paddle_input                  │
│  │ keyboard_controller│──────────────────────┐              │
│  └───────────────────┘                       ▼              │
│                                   ┌──────────────────┐      │
│                                   │   pygame_pong    │      │
│                                   │  (Main Node)     │      │
│                                   └────────┬─────────┘      │
│                        ┌───────────────────┤                │
│                        │                   │                │
│     /pong/game_state   ▼    /pong/score_event               │
│   ┌──────────────────────┐        ▼                         │
│   │   pong_visualizer    │  (logged to terminal)            │
│   │  (rviz2 MarkerArray) │                                  │
│   └──────────────────────┘                                  │
│            │ /pong/markers                                   │
│            ▼                                                 │
│         [rviz2]                                              │
└─────────────────────────────────────────────────────────────┘
```

### ROS 2 Nodes

| Node | File | Role |
|---|---|---|
| `/pygame_pong` | `pygame_pong.py` | Main game logic, GUI, publisher |
| `/keyboard_controller` | `keyboard_controller.py` | Network P2 keyboard input |
| `/pong_visualizer` | `visualizer.py` | rviz2 MarkerArray publisher |

### ROS 2 Topics

| Topic | Message Type | Publisher | Subscriber |
|---|---|---|---|
| `/pong/game_state` | `pong_msgs/PongGameState` | pygame_pong | pong_visualizer |
| `/pong/paddle_input` | `pong_msgs/PongGameState` | keyboard_controller | pygame_pong |
| `/pong/score_event` | `pong_msgs/PongScore` | pygame_pong | — |
| `/pong/markers` | `visualization_msgs/MarkerArray` | pong_visualizer | rviz2 |

---

## 📨 Custom Messages

### `pong_msgs/msg/PongGameState.msg`
```
# Ball state
float32 ball_x          # Ball X position (pixels)
float32 ball_y          # Ball Y position (pixels)
float32 ball_vel_x      # Ball X velocity
float32 ball_vel_y      # Ball Y velocity

# Paddle positions
float32 paddle1_y       # Player 1 paddle Y position
float32 paddle2_y       # Player 2 paddle Y position

# Score
int32 score_player1     # Player 1 score
int32 score_player2     # Player 2 score

# Game status: 0=waiting, 1=playing, 2=player1 wins, 3=player2 wins
int32 game_status
```

### `pong_msgs/msg/PongScore.msg`
```
int32 player_scored     # 1=player1, 2=player2
int32 score_player1     # Current score player 1
int32 score_player2     # Current score player 2
string event_type       # "score", "win", "start"
string winner           # "player1", "player2", "ai", ""
```

---

## 💻 Requirements

### System
- Windows 10/11 with WSL2, or native Ubuntu 24.04
- At least 10GB free disk space

### Software
- ROS 2 Jazzy
- Python 3.12
- pygame 2.5.2
- numpy

---

## 🚀 Installation

### Step 1: Install WSL2 (Windows only)
Open PowerShell as Administrator:
```powershell
wsl --install -d Ubuntu-24.04
```
Restart your computer when prompted.

### Step 2: Fix DNS (WSL2 only)
```bash
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

### Step 3: Install ROS 2 Jazzy
```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu noble main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-jazzy-desktop
sudo apt install -y python3-colcon-common-extensions python3-pip
```

### Step 4: Setup ROS 2 environment
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 5: Install Python dependencies
```bash
sudo apt install -y python3-pygame python3-numpy
```

### Step 6: Clone and build
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/sokuntheary-chheng/matlab_group8_ping_pong.git .
cd ~/ros2_ws
colcon build
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 7: Run the game 🎮
```bash
ros2 run pong_game pygame_pong
```

---

## 🎮 How to Play

### Single Player (vs AI)
1. Select **"Single Player"** from the home screen
2. Controls:
   - **W** → Move paddle up
   - **S** → Move paddle down
3. First to reach the **Winning Score** wins (default: 5, changeable in Settings)
4. Ball speeds up with every paddle hit!
5. Press **ESC** to return home, **R** to restart

### Two Players (Same PC)
1. Select **"Two Players"** from the home screen
2. Controls:

| Player | Up | Down |
|---|---|---|
| Player 1 (Left — GREEN) | W | S |
| Player 2 (Right — RED) | ↑ | ↓ |

### Network Mode (Across 2 PCs)

Both PCs must be on the **same WiFi** and have the same `ROS_DOMAIN_ID` (default: 0).

**Host PC (Player 1):**
1. Launch the game normally:
   ```bash
   ros2 run pong_game pygame_pong
   ```
2. Select **"Across 2 PCs"** → Press **SPACE** to start
3. Control your paddle with **W / S**
4. Your paddle is on the **LEFT side (GREEN)**

**Guest PC (Player 2):**
1. Clone and build the repo (see Installation)
2. Run the guest client:
   ```bash
   ros2 run pong_game pong_client
   ```
3. You will see the **full game display** and control your paddle with **W / S**
4. Your paddle is on the **RIGHT side (RED)**

**If Guest paddle does not respond:**
```bash
# Run on both PCs before launching
export ROS_DOMAIN_ID=0
```

### General Controls

| Key | Action |
|---|---|
| ESC | Return to Home screen |
| R | Restart current game |
| W / S | Move paddle (Player 1 or Guest) |
| ↑ / ↓ | Move paddle (Player 2 local) |

---

## ⚙️ Settings

Access settings from the **Home screen → Settings button**.

| Tab | Options |
|---|---|
| **Gameplay** | Ball starting speed, speed increase per hit, winning score (5/10/15/20), difficulty (Easy/Normal/Hard) |
| **Audio** | Master volume, BGM volume, SFX volume, Mute toggle |
| **Display** | FPS counter, particle effects, court lines |
| **Controls** | View current key bindings |
| **Accessibility** | Colorblind mode, high contrast mode |

Settings are saved automatically to `~/.pong_settings.json`.

---

## 📁 Project Structure

```
src/
├── pong_msgs/                    # Custom message package
│   ├── msg/
│   │   ├── PongGameState.msg    # Main game state message
│   │   └── PongScore.msg        # Score event message
│   ├── CMakeLists.txt
│   └── package.xml
│
└── pong_game/                    # Game package
    ├── pong_game/
    │   ├── __init__.py
    │   ├── pygame_pong.py        # Main game + GUI + ROS 2 node
    │   ├── keyboard_controller.py # Network P2 keyboard input (terminal only)
    │   ├── pong_client.py        # Guest client with full game display
    │   ├── visualizer.py         # rviz2 MarkerArray publisher
    │   ├── sound_gen.py          # Programmatic sound + BGM generator
    │   ├── settings.py           # Settings load/save (JSON)
    │   └── game_logic.py         # Standalone game logic node
    ├── launch/
    │   └── pong.launch.py        # Launch all 3 nodes
    ├── package.xml
    ├── setup.py
    └── setup.cfg
```

---

## 🔧 Troubleshooting

### Game window does not appear (WSL2)
```bash
# Make sure DISPLAY is set
echo $DISPLAY
# Should show :0 or similar
# If empty, install an X server like VcXsrv or use Windows 11 WSLg
```

### ROS 2 not found
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

### Build fails — pong_msgs not found
```bash
cd ~/ros2_ws
colcon build --packages-select pong_msgs
source install/setup.bash
colcon build --packages-select pong_game
source install/setup.bash
```

### pygame AVX2 warning
This is just a warning, not an error. The game runs fine.

### Network mode — Guest paddle not responding
```bash
# Run on BOTH PCs
export ROS_DOMAIN_ID=0
# Then re-source and re-run
source ~/ros2_ws/install/setup.bash
ros2 run pong_game pong_client
```

### Verify ROS 2 topics are active
```bash
ros2 topic list
# Should show: /pong/game_state /pong/paddle_input /pong/score_event /pong/markers

ros2 topic hz /pong/game_state
# Should show ~20 Hz
```

---

## 📊 Performance

| Metric | Value |
|---|---|
| Game update rate | 20 Hz |
| Render rate | 60 FPS |
| Topic latency | < 50ms |
| Nodes | 3 |
| Topics | 4 |
| Custom messages | 2 |

---

**Course:** Seminar and Project IV
**Lecturer:** Dr. SRANG Sarot
**Institution:** Institute of Technology of Cambodia (ITC)
**Year:** 2 | **Semester:** 2 | **Group:** 8

---

<div align="center">
Made with ❤️ using ROS 2 Jazzy + pygame
</div>