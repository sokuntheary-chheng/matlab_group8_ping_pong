# WebSocket Debugging & Troubleshooting Guide

## 🔧 Diagnostic Tools

### 1. WebSocket Connection Test
```bash
python3 test_websocket.py [ws://server:port]
```

**Expected Output:**
```
Connecting to WebSocket server at ws://localhost:8765...
✓ Connected to WebSocket server!
Sending command 1/5: {'type': 'paddle_move', 'player': 2, 'paddle_y': -1.5}
...
✓ All commands sent successfully!
TEST PASSED ✓
```

### 2. Check Port Availability
```bash
# Linux/WSL
sudo netstat -tulpn | grep 8765

# macOS
lsof -i :8765

# Windows PowerShell
netstat -ano | findstr :8765
```

### 3. ROS 2 Topic Monitoring
```bash
# Monitor paddle input messages
ros2 topic echo /pong/paddle_input

# Monitor game state
ros2 topic echo /pong/game_state

# Check node activity
ros2 node list
```

### 4. Check Network Connectivity
```bash
# Ping host from client
ping [host-ip]

# Test port connectivity
nc -zv [host-ip] 8765  # Linux/macOS
Test-NetConnection -ComputerName [host-ip] -Port 8765  # Windows
```

---

## 🐛 Common Problems & Solutions

### Problem 1: "Connection refused" Error

**Symptoms:**
```
[pong_client] WebSocket connection attempt 1/10 failed: 
[Errno 111] Connection refused
```

**Root Causes:**
- ❌ Host is not running
- ❌ WebSocket server failed to start
- ❌ Wrong IP address
- ❌ Wrong port number

**Solutions:**
1. Verify host is running:
   ```bash
   # Check if pygame_pong process is running
   ps aux | grep pygame_pong
   ```

2. Check WebSocket server started:
   ```bash
   # Look for this in host console
   [pygame_pong] WebSocket server started on ws://0.0.0.0:8765
   ```

3. Verify IP address:
   ```bash
   # On host, get IP
   hostname -I
   
   # On client, use this IP
   export PONG_SERVER_URL=ws://[host-ip]:8765
   ```

4. Test port directly:
   ```bash
   nc -zv [host-ip] 8765
   ```

---

### Problem 2: Paddle Not Moving

**Symptoms:**
- Keyboard input works (game responds to ESC key)
- Paddle position doesn't change with W/S
- No paddle movement animation

**Root Causes:**
- ❌ WebSocket connection not established
- ❌ Paddle movement commands not being sent
- ❌ Game logic not receiving messages
- ❌ Game status not running (status != 1)

**Solutions:**

1. **Check WebSocket connection status:**
   ```bash
   # Look for this in client console
   [pong_client] Connected to WebSocket server at ws://localhost:8765
   ```

2. **Verify paddle input is being published:**
   ```bash
   ros2 topic echo /pong/paddle_input --once
   # Should show paddle2_y values changing
   ```

3. **Check game status:**
   ```bash
   ros2 topic echo /pong/game_state | grep game_status
   # Should show game_status: 1 (running)
   # 0 = waiting for game to start
   # 1 = game running
   # 2 = player 1 wins
   # 3 = player 2 wins
   ```

4. **Verify keyboard handler thread:**
   ```bash
   # In client console, you should see:
   [pong_client] Pong Client started! You are Player 2 (RIGHT paddle)
   [pong_client] Controls: W = Up  |  S = Down  |  Q = Quit
   ```

5. **Test with manual ROS command:**
   ```bash
   # Send paddle command directly via ROS
   ros2 topic pub /pong/paddle_input pong_msgs/PongGameState \
     "paddle2_y: 1.5"
   # Check if paddle moves
   ```

---

### Problem 3: Connection Keeps Dropping

**Symptoms:**
```
[pong_client] WebSocket connection closed by server
[pong_client] WebSocket connection attempt 2/10 failed...
```

**Root Causes:**
- ❌ Network instability
- ❌ Host crash or hang
- ❌ Firewall blocking traffic
- ❌ Router dropping idle connections

**Solutions:**

1. **Check network stability:**
   ```bash
   # Monitor latency
   ping -c 100 [host-ip] | tail -5
   # Should show low packet loss and consistent latency
   ```

2. **Increase retry parameters:**
   Edit `pong_client.py`:
   ```python
   max_retries = 20         # Increase from 10
   retry_delay = 3          # Increase from 2
   ```

3. **Check firewall rules:**
   ```bash
   # Linux UFW
   sudo ufw allow 8765/tcp
   
   # Linux iptables
   sudo iptables -A INPUT -p tcp --dport 8765 -j ACCEPT
   
   # Windows Firewall (PowerShell as admin)
   New-NetFirewallRule -DisplayName "Allow Pong WebSocket" `
     -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8765
   ```

4. **Check system logs:**
   ```bash
   # Linux
   journalctl -u pong --follow
   
   # ROS 2
   ros2 run rclpy rclpy.qos
   ```

---

### Problem 4: "Address already in use" Error

**Symptoms:**
```
[pygame_pong] Error starting WebSocket server: Address already in use
```

**Root Causes:**
- ❌ Previous game process still holding port 8765
- ❌ Another application using port 8765

**Solutions:**

1. **Find and kill process:**
   ```bash
   # Linux/WSL
   lsof -i :8765 | awk 'NR>1 {print $2}' | xargs kill -9
   
   # Windows PowerShell
   (Get-NetTCPConnection -LocalPort 8765).OwningProcess | 
     ForEach-Object { Stop-Process -Id $_ -Force }
   ```

2. **Wait for port to be released:**
   ```bash
   # Linux - wait for TIME_WAIT state to clear (usually 60 seconds)
   netstat -an | grep 8765
   # Wait and retry
   sleep 60
   ```

3. **Change port (temporary workaround):**
   Edit `pygame_pong.py`:
   ```python
   self.ws_server = PongWebSocketServer(self, host="0.0.0.0", port=9000)
   ```
   Then on client:
   ```bash
   export PONG_SERVER_URL=ws://localhost:9000
   ```

---

### Problem 5: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'websockets'
```

**Solutions:**

1. **Install websockets package:**
   ```bash
   pip install websockets
   ```

2. **Rebuild package:**
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select pong_game
   source install/setup.bash
   ```

3. **Verify installation:**
   ```bash
   python3 -c "import websockets; print('websockets OK')"
   ```

---

### Problem 6: Game Shows "Waiting for Host"

**Symptoms:**
- Client screen shows "Waiting for Host to start the game..."
- Game state doesn't update

**Root Causes:**
- ❌ Host hasn't started game (game_status = 0)
- ❌ Different network mode settings
- ❌ Host not publishing game_state messages

**Solutions:**

1. **Check host is running game:**
   ```bash
   ros2 topic echo /pong/game_state | grep game_status
   # Should show game_status: 1 (running)
   ```

2. **Start game on host:**
   - Press SPACE or select game mode to start

3. **Monitor game state:**
   ```bash
   ros2 topic hz /pong/game_state
   # Should show >10 Hz message rate
   ```

---

## 📊 Advanced Diagnostics

### Enable Verbose Logging

**Client:**
```bash
export ROS_LOG_LEVEL=DEBUG
ros2 run pong_game pong_client
```

**Host:**
```bash
export ROS_LOG_LEVEL=DEBUG
ros2 run pong_game pygame_pong
```

### Monitor All ROS Topics
```bash
# Show all topics
ros2 topic list

# Show topic rates
ros2 topic hz /pong/paddle_input
ros2 topic hz /pong/game_state

# Monitor message traffic
ros2 topic echo /pong/paddle_input &
ros2 topic echo /pong/game_state &
```

### Check Node Graph
```bash
# Show node connectivity
ros2 node list
ros2 node info pong_client
ros2 node info pygame_pong

# Visualize with rqt
rqt_graph
```

### Performance Monitoring
```bash
# Monitor CPU/memory usage
top -p $(pgrep -f pong)

# Check thread count
ps -L -p $(pgrep -f pong) | wc -l
```

---

## 🔍 Debugging Checklist

When something goes wrong, check in order:

- [ ] **Connection Level**
  - [ ] Host PC is running `pygame_pong`
  - [ ] WebSocket server started (check logs)
  - [ ] Port 8765 is open and listening
  - [ ] Client can ping host IP
  - [ ] Test connection: `python3 test_websocket.py`

- [ ] **Client Level**
  - [ ] Client process is running
  - [ ] WebSocket connection shows "Connected"
  - [ ] Keyboard input works (ESC key responds)
  - [ ] Console shows no errors or warnings

- [ ] **Network Level**
  - [ ] Network connectivity (no packet loss)
  - [ ] Firewall allows port 8765
  - [ ] No proxy/VPN interference
  - [ ] IP addresses are correct

- [ ] **ROS Level**
  - [ ] `/pong/paddle_input` topic exists
  - [ ] `/pong/game_state` topic publishing
  - [ ] Game status = 1 (running)
  - [ ] Messages are being received/sent

- [ ] **Application Level**
  - [ ] Game UI visible on client
  - [ ] Paddle renders correctly
  - [ ] Ball physics working
  - [ ] Score updates correctly

---

## 📞 Getting Help

If problems persist:

1. **Collect logs:**
   ```bash
   # Capture full output
   ros2 run pong_game pygame_pong 2>&1 | tee host.log
   ros2 run pong_game pong_client 2>&1 | tee client.log
   ```

2. **Run diagnostics:**
   ```bash
   python3 test_websocket.py ws://[host-ip]:8765
   ros2 topic echo /pong/paddle_input
   ```

3. **Check environment:**
   ```bash
   echo $PONG_SERVER_URL
   echo $ROS_DOMAIN_ID
   ros2 env
   ```

4. **Document issue:**
   - Include error message
   - Include log output
   - Describe steps to reproduce
   - List environment (OS, ROS version, Python version)

---

## 🧪 Test Scenarios

### Scenario 1: Local Testing (Same Computer)
```bash
# Terminal 1: Start host
ros2 launch pong_game pong.launch.py

# Terminal 2: Start client
export PONG_SERVER_URL=ws://localhost:8765
ros2 run pong_game pong_client

# Terminal 3: Monitor
ros2 topic echo /pong/paddle_input
```

### Scenario 2: Remote Testing (Different Computers)
```bash
# On host
hostname -I  # Get IP address
ros2 launch pong_game pong.launch.py

# On client
export PONG_SERVER_URL=ws://[host-ip]:8765
ros2 run pong_game pong_client
```

### Scenario 3: Network Stress Testing
```bash
# Simulate network delay
sudo tc qdisc add dev eth0 root netem delay 100ms

# Add packet loss
sudo tc qdisc change dev eth0 root netem loss 5%

# Remove delay
sudo tc qdisc del dev eth0 root
```

---

## 💡 Pro Tips

1. **Use screen/tmux** for multiple terminals:
   ```bash
   screen -S pong_host
   # Ctrl-A D to detach
   screen -S pong_client
   ```

2. **Create launch script:**
   ```bash
   #!/bin/bash
   export PONG_SERVER_URL=ws://192.168.1.100:8765
   ros2 run pong_game pong_client
   ```

3. **Monitor with watch:**
   ```bash
   watch -n 1 'ros2 topic hz /pong/paddle_input'
   ```

4. **Log all output:**
   ```bash
   ros2 run pong_game pong_client 2>&1 | tee pong.log
   tail -f pong.log
   ```

---

**Last Updated**: 2024  
**Status**: Complete Debugging Guide ✓
