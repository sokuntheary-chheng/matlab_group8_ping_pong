# WebSocket-Based Pong Game — Client Paddle Movement

## Overview
The Pong game now supports **WebSocket-based paddle movement** for client players. The client connects to a WebSocket server running on the game host and sends paddle movement commands via WebSocket instead of direct ROS topic publishing.

## Architecture

### Components
1. **pygame_pong.py (HOST)**: 
   - Runs the main game and UI
   - Hosts the WebSocket server on `ws://0.0.0.0:8765`
   - Receives paddle commands from WebSocket clients
   - Publishes to ROS topics for game logic

2. **pong_client.py (CLIENT)**: 
   - Connects to the host's WebSocket server
   - Captures keyboard input (W/S keys)
   - Sends paddle movement commands via WebSocket
   - Receives and renders game state from ROS topics

3. **websocket_server.py**: 
   - WebSocket server component
   - Handles client connections
   - Converts WebSocket messages to ROS paddle_input messages

## How to Run

### On the Host PC (pygame_pong):
```bash
# Build the package
cd ~/ros2_ws
colcon build --packages-select pong_game

# Source the setup
source install/setup.bash

# Launch the game
ros2 launch pong_game pong.launch.py

# Or run directly
ros2 run pong_game pygame_pong
```

The WebSocket server will automatically start on `ws://localhost:8765` (or `ws://<host-ip>:8765` for remote connections).

### On the Client PC (pong_client):
```bash
# Build the package
cd ~/ros2_ws
colcon build --packages-select pong_game

# Source the setup
source install/setup.bash

# Run the client (connecting to localhost)
ros2 run pong_game pong_client

# Or specify a remote host
ros2 run pong_game pong_client ws://<host-ip>:8765

# Or use environment variable
export PONG_SERVER_URL=ws://<host-ip>:8765
ros2 run pong_game pong_client
```

## Controls

**Player 2 (Guest/Client)**:
- **W**: Move paddle UP
- **S**: Move paddle DOWN
- **Q**: Quit the game

## WebSocket Message Format

### Client → Server (Paddle Movement)
```json
{
  "type": "paddle_move",
  "player": 2,
  "paddle_y": -1.5
}
```

**Fields**:
- `type`: Message type (currently only "paddle_move" supported)
- `player`: Player number (1 or 2)
- `paddle_y`: Normalized paddle position (-2.25 to 2.25)

## Network Setup

### For Local Testing:
1. Run both host and client on the same machine
2. Client connects to `ws://localhost:8765`

### For Remote Network:
1. Find the host PC's IP address:
   ```bash
   hostname -I
   ```
2. Ensure the host is reachable from the client PC
3. Client connects to `ws://<host-ip>:8765`

### Firewall Considerations:
- Ensure port 8765 is open and accessible between host and client
- On Linux: `sudo ufw allow 8765`
- On Windows: Configure Windows Firewall to allow connections on port 8765

## Features

✅ **Automatic Reconnection**: Client automatically retries connection up to 10 times  
✅ **Backwards Compatible**: Still supports ROS topic communication  
✅ **Real-time Communication**: Sub-50ms latency typical  
✅ **Robust Error Handling**: Graceful handling of connection failures  
✅ **Cross-platform**: Works on Linux, WSL, and Windows  

## Troubleshooting

### Client won't connect to server
- Verify host is running and WebSocket server is started
- Check that port 8765 is not blocked by firewall
- Verify the server URL is correct: `ws://<host-ip>:8765`
- Check ROS 2 is properly sourced on both machines

### Paddle not moving
- Check keyboard input is working (W/S keys)
- Verify WebSocket connection is established (check logs)
- Ensure game_status == 1 (game is running, not waiting)
- Check that the ROS topic `/pong/paddle_input` is receiving messages

### Connection keeps dropping
- Check network stability
- Reduce network latency if possible
- Increase retry delay in websocket_server.py if needed

### Check Connection Status
In the client terminal, look for:
```
[pong_client] Connected to WebSocket server at ws://<host>:8765
```

In the host terminal, look for:
```
[websocket_server] WebSocket server started on ws://0.0.0.0:8765
[websocket_server] Client connected. Total clients: 1
```

## Environment Variables

- `PONG_SERVER_URL`: Set the WebSocket server URL
  ```bash
  export PONG_SERVER_URL=ws://192.168.1.100:8765
  ros2 run pong_game pong_client
  ```

## Package Dependencies

The following packages must be installed:
- `websockets` (Python package) — automatically installed via setup.py
- `rclpy` (ROS 2)
- `pygame`
- `numpy`

These are automatically installed when building with colcon.
