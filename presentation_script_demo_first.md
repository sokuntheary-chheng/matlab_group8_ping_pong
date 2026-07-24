# ROS 2 Pong Game — Demo-First Presentation Script

## Goal of the presentation
You will first show the game running, then show the ROS graph and topics, and finally walk through the code.

---

## Part 1 — Demo first (3–4 minutes)

### 1. Start with the architecture in one sentence
Say:

"This project is a ROS 2-based Pong game where input is published as messages, the game node processes those messages, and the visualizer subscribes to the updated game state."

### 2. Run the single-player game
Say:

"First I will run the single-player mode. In this mode, the game runs locally and the player controls the left paddle with W and S."

What to do:
- Launch the game locally:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/src/install/setup.bash
ros2 run pong_game pygame_pong
```

What to say while playing:
- "When I press W, the game updates the paddle position."
- "The game logic is running inside the same node, so this is local processing."

### 3. Run the two-player mode
Say:

"Next I will run the two-player mode. Here, one player uses W/S and the other uses the arrow keys."

What to do:
- In the same game window, choose the two-player mode from the home screen.

What to say while playing:
- "Here, the game still runs locally, but the input is split between two players."
- "The same node handles both inputs and updates the game state."

### 4. Show the ROS graph and topics
Say:

"Now I will show the ROS side of the project using rqt_graph and the topic list."

Run:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/src/install/setup.bash
ros2 node list
ros2 topic list
rqt_graph
```

What you will likely see:
- Nodes: /pygame_pong, /keyboard_controller, /pong_visualizer, /parameter_events, /rosout
- Topics: /pong/paddle_input, /pong/game_state, /pong/score_event, /pong/markers

Say:

"The graph shows the main communication structure. The input node publishes paddle movement, the game node subscribes and updates the game, and the visualizer subscribes to the game state."

---

## Part 2 — Code walkthrough (5–6 minutes)

### 1. How many nodes/functions are there?
Say:

"There are four main ROS nodes in the project:
- pygame_pong
- keyboard_controller
- visualizer
- pong_client (used for the two-PC network mode)

There are also several important functions inside these nodes."

### 2. Node and function overview
Use these code locations:

- [src/pong_game/setup.py](src/pong_game/setup.py)
  - This registers the node entry points.
  - Relevant lines: the console_scripts block.

- [src/pong_game/pong_game/pygame_pong.py](src/pong_game/pong_game/pygame_pong.py)
  - Main node class: PongNode
  - Relevant functions:
    - __init__() at the top of the class
    - publish_state()
    - state_callback()
    - paddle_callback()
    - update_game()
    - main()
  - Relevant lines to show:
    - publisher creation for /pong/game_state and /pong/score_event
    - subscription to /pong/paddle_input
    - the main game loop in update_game()

- [src/pong_game/pong_game/keyboard_controller.py](src/pong_game/pong_game/keyboard_controller.py)
  - Main node class: KeyboardController
  - Relevant functions:
    - __init__()
    - read_keyboard()
    - publish_paddles()
    - main()

- [src/pong_game/pong_game/pong_client.py](src/pong_game/pong_game/pong_client.py)
  - Main node class: PongClient
  - Relevant functions:
    - __init__()
    - state_callback()
    - publish_paddles()
    - read_keyboard()
    - main()

- [src/pong_game/pong_game/visualizer.py](src/pong_game/pong_game/visualizer.py)
  - Main node class: PongVisualizer
  - Relevant functions:
    - __init__()
    - make_marker()
    - state_callback()
    - main()

- [src/pong_game/pong_game/network_controls.py](src/pong_game/pong_game/network_controls.py)
  - Helper for client-side movement stability.

### 3. What is the difference between each function?
Say:

- __init__() sets up the node, publishers, subscribers, and initial variables.
- read_keyboard() receives key presses.
- publish_paddles() or publish_state() sends messages to topics.
- state_callback() receives incoming game-state data.
- paddle_callback() receives input from the remote client or controller.
- update_game() applies the game rules and changes the on-screen state.
- main() starts the node and runs the event loop.

### 4. Node-by-node explanation
Say each one clearly:

- pygame_pong
  - Function: main game logic and GUI
  - Input: receives /pong/paddle_input
  - Output: publishes /pong/game_state and /pong/score_event

- keyboard_controller
  - Function: reads keyboard input from the terminal
  - Input: keyboard keys
  - Output: publishes /pong/paddle_input

- visualizer
  - Function: converts game state into visualization markers
  - Input: subscribes to /pong/game_state
  - Output: publishes /pong/markers

- pong_client
  - Function: client-side game window for two-PC play
  - Input: receives /pong/game_state and keyboard input
  - Output: publishes /pong/paddle_input to the host

### 5. Topic design and publish/subscribe map
Say:

- /pong/paddle_input
  - Purpose: carries paddle movement data
  - Publisher: keyboard_controller and pong_client
  - Subscriber: pygame_pong
  - Data inside: paddle positions, usually paddle1_y and paddle2_y

- /pong/game_state
  - Purpose: carries the full game state
  - Publisher: pygame_pong
  - Subscriber: visualizer and the client-side game node in network mode
  - Data inside: ball position, ball velocity, paddle positions, score, game_status

- /pong/score_event
  - Purpose: carries scoring and win events
  - Publisher: pygame_pong
  - Subscriber: optional listeners / logging

- /pong/markers
  - Purpose: carries visualization markers for RViz
  - Publisher: visualizer
  - Subscriber: rviz2 or visualization tools

### 6. Data flow direction
Say:

"This is a bottom-up data-processing structure from a ROS perspective: input is received at the edge, processed in the main game node, and then forwarded to other nodes."

Explain:
- The game starts with input.
- The game node updates the game state.
- The visualizer consumes that state and creates visuals.
- The system is not just a simple one-way pipeline; it is a publish/subscribe system with multiple connected nodes.

### 7. Overall architecture and logic flow
Say:

"The logical process is:
1. User presses a key.
2. The input node publishes that input message.
3. pygame_pong receives the message and updates the ball/paddle positions.
4. pygame_pong publishes the new game state.
5. The visualizer receives the game state and publishes markers.
6. The GUI displays the game and the visualization tool displays the markers."

### 8. Visualizer-specific explanation
Say:

"The visualizer is responsible for the visualization part of the system. It subscribes to /pong/game_state, converts the game state into Marker objects, and publishes them to /pong/markers."

Important note:
- It is not using HTML here.
- It converts the game data into ROS visualization messages.

### 9. What to say while playing the demo
Use these lines:

- Single-player:
  "When I press W, the input is processed by the game node and the paddle moves."

- Two-player:
  "In two-player mode, both players’ inputs are handled by the same main game node."

- Network/client mode:
  "When the client presses W or S, that input is published to /pong/paddle_input and received by the host game node, which updates the remote paddle position."

### 10. What to say at the end
Say:

"In summary, this project shows how a game can be built as a ROS 2 distributed system. The main idea is that nodes communicate through topics, and the game state flows from input to processing to visualization. If I had more time, I would improve the network synchronization and make the visualizer more polished."

---

## Extra note for the code display
When you show the code, point to these exact files and explain what each section does:
- [src/pong_game/pong_game/pygame_pong.py](src/pong_game/pong_game/pygame_pong.py)
- [src/pong_game/pong_game/keyboard_controller.py](src/pong_game/pong_game/keyboard_controller.py)
- [src/pong_game/pong_game/pong_client.py](src/pong_game/pong_game/pong_client.py)
- [src/pong_game/pong_game/visualizer.py](src/pong_game/pong_game/visualizer.py)
- [src/pong_game/setup.py](src/pong_game/setup.py)
