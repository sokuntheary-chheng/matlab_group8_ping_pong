#!/usr/bin/env python3
"""
Pong WebSocket Implementation Verification Script
Checks all components are properly installed and configured.
"""
import sys
import subprocess
import json
from pathlib import Path


def check(condition, description):
    """Print check result"""
    status = "✓" if condition else "✗"
    print(f"{status} {description}")
    return condition


def main():
    print("=" * 70)
    print("Pong WebSocket Implementation Verification")
    print("=" * 70)
    print()

    all_good = True

    # 1. Check Python packages
    print("📦 Checking Python Dependencies:")
    print("-" * 70)

    packages = {
        "asyncio": "Async I/O support",
        "pygame": "Graphics rendering",
        "numpy": "Numerical computing"
    }

    optional_packages = {
        "websockets": "WebSocket support (will be installed by colcon)",
        "rclpy": "ROS 2 client (will be available in ROS 2 environment)"
    }

    for package, description in packages.items():
        try:
            __import__(package)
            all_good &= check(True, f"{package:15} - {description}")
        except ImportError:
            all_good &= check(False, f"{package:15} - {description}")

    print()
    print("Optional Packages (will be available after ROS 2 build):")
    for package, description in optional_packages.items():
        try:
            __import__(package)
            check(True, f"{package:15} - {description}")
        except ImportError:
            check(False, f"{package:15} - {description} ⚠ Will be installed")

    print()

    # 2. Check files
    print("📁 Checking Implementation Files:")
    print("-" * 70)

    files_to_check = [
        ("pong_game/pong_client.py", "Client with WebSocket support"),
        ("pong_game/pygame_pong.py", "Host with WebSocket server"),
        ("pong_game/websocket_server.py", "WebSocket server component"),
        ("setup.py", "Package configuration"),
        ("test_websocket.py", "Connection test utility"),
        ("WEBSOCKET_GUIDE.md", "Usage documentation"),
        ("QUICK_REFERENCE.md", "Quick start guide"),
        ("DEBUGGING_GUIDE.md", "Troubleshooting guide"),
    ]

    script_dir = Path(__file__).parent
    for filepath, description in files_to_check:
        full_path = script_dir / filepath
        exists = full_path.exists()
        all_good &= check(exists, f"{filepath:40} - {description}")
        if exists and filepath.endswith(".py"):
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    if filepath == "pong_game/pygame_pong.py":
                        # For pygame_pong, check for websocket_server import
                        if "websocket_server" in content:
                            check(True, f"  └─ WebSocket server imports found")
                        else:
                            all_good &= check(False, f"  └─ WebSocket server imports missing")
                    elif "websockets" in content or "websocket_server" in content:
                        check(True, f"  └─ WebSocket imports found")
                    else:
                        all_good &= check(False, f"  └─ WebSocket imports missing")
            except Exception as e:
                all_good &= check(False, f"  └─ Could not read file: {e}")

    print()

    # 3. Check ROS 2
    print("🤖 Checking ROS 2 Setup:")
    print("-" * 70)

    try:
        result = subprocess.run(["ros2", "--version"], capture_output=True, text=True, timeout=5)
        ros2_ok = result.returncode == 0
        all_good &= check(ros2_ok, "ROS 2 command available")
        if ros2_ok:
            version = result.stdout.strip()
            print(f"  └─ {version}")
    except Exception as e:
        all_good &= check(False, f"ROS 2 command available - {e}")

    print()

    # 4. Check code quality
    print("✨ Checking Code Quality:")
    print("-" * 70)

    # Check pong_client.py for required methods
    try:
        with open(script_dir / "pong_game/pong_client.py", 'r') as f:
            client_code = f.read()
            all_good &= check("send_paddle_command" in client_code,
                              "pong_client has send_paddle_command method")
            all_good &= check("websocket_client_main" in client_code,
                              "pong_client has websocket_client_main method")
            all_good &= check("run_websocket_client" in client_code,
                              "pong_client has run_websocket_client method")
    except Exception as e:
        all_good &= check(False, f"Could not analyze pong_client.py - {e}")

    # Check pygame_pong.py for WebSocket integration
    try:
        with open(script_dir / "pong_game/pygame_pong.py", 'r') as f:
            host_code = f.read()
            all_good &= check("PongWebSocketServer" in host_code,
                              "pygame_pong imports WebSocket server")
            all_good &= check("setup_websocket_server" in host_code,
                              "pygame_pong has setup_websocket_server method")
            all_good &= check("websocket_server" in host_code,
                              "pygame_pong imports from websocket_server module")
    except Exception as e:
        all_good &= check(False, f"Could not analyze pygame_pong.py - {e}")

    # Check websocket_server.py
    try:
        with open(script_dir / "pong_game/websocket_server.py", 'r') as f:
            server_code = f.read()
            all_good &= check("PongWebSocketServer" in server_code,
                              "websocket_server has PongWebSocketServer class")
            all_good &= check("handle_client" in server_code,
                              "websocket_server has handle_client method")
            all_good &= check("process_message" in server_code,
                              "websocket_server has process_message method")
    except Exception as e:
        all_good &= check(False, f"Could not analyze websocket_server.py - {e}")

    print()

    # 5. Network checks
    print("🌐 Checking Network Configuration:")
    print("-" * 70)

    try:
        result = subprocess.run(["python3", "-c", "import socket; print(socket.gethostbyname(socket.gethostname()))"],
                                capture_output=True, text=True, timeout=5)
        localhost_ok = result.returncode == 0
        all_good &= check(localhost_ok, "Network resolution working")
        if localhost_ok:
            ip = result.stdout.strip()
            print(f"  └─ Local IP: {ip}")
    except Exception as e:
        all_good &= check(False, f"Network resolution - {e}")

    print()

    # 6. Summary
    print("=" * 70)
    if all_good:
        print("✅ ALL CHECKS PASSED - Implementation is ready!")
        print()
        print("Next steps:")
        print("1. Start host:   ros2 launch pong_game pong.launch.py")
        print("2. Start client: ros2 run pong_game pong_client")
        print("3. Test:         python3 test_websocket.py")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please fix issues above")
        print()
        print("Troubleshooting:")
        print("1. Install missing packages: pip install websockets")
        print("2. Rebuild package: colcon build --packages-select pong_game")
        print("3. Source ROS 2: source install/setup.bash")
        print("4. Check DEBUGGING_GUIDE.md for detailed help")
        return 1


if __name__ == "__main__":
    sys.exit(main())
