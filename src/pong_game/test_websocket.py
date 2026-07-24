#!/usr/bin/env python3
"""
Simple WebSocket client test for Pong game paddle movement.
Tests the WebSocket connection and sends paddle movement commands.
"""
import asyncio
import json
import sys
import websockets


async def test_websocket_connection(server_url: str):
    """Test WebSocket connection and send paddle movement commands"""
    print(f"Connecting to WebSocket server at {server_url}...")
    
    try:
        async with websockets.connect(server_url) as websocket:
            print("✓ Connected to WebSocket server!")
            
            # Test paddle movement commands
            commands = [
                {"type": "paddle_move", "player": 2, "paddle_y": -1.5},
                {"type": "paddle_move", "player": 2, "paddle_y": -0.9},
                {"type": "paddle_move", "player": 2, "paddle_y": 0.0},
                {"type": "paddle_move", "player": 2, "paddle_y": 0.9},
                {"type": "paddle_move", "player": 2, "paddle_y": 1.5},
            ]
            
            for i, cmd in enumerate(commands):
                print(f"\nSending command {i+1}/5: {cmd}")
                await websocket.send(json.dumps(cmd))
                await asyncio.sleep(0.5)
            
            print("\n✓ All commands sent successfully!")
            print("✓ WebSocket connection is working correctly!")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print("✗ WebSocket connection failed!")
        return False


def main():
    """Main test function"""
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    
    print("=" * 60)
    print("Pong WebSocket Connection Test")
    print("=" * 60)
    print(f"Server URL: {server_url}")
    print()
    
    success = asyncio.run(test_websocket_connection(server_url))
    
    print("\n" + "=" * 60)
    if success:
        print("TEST PASSED ✓")
        sys.exit(0)
    else:
        print("TEST FAILED ✗")
        print("\nTroubleshooting:")
        print("1. Ensure the host PC has the game running")
        print("2. Verify the server URL is correct")
        print("3. Check firewall settings for port 8765")
        print("4. Ensure both machines are on the same network")
        sys.exit(1)


if __name__ == "__main__":
    main()
