"""
WebSocket Server for Pong Game
Handles client paddle movement commands and publishes to ROS topic.
"""
import asyncio
import json
import websockets
from typing import Set
from rclpy.node import Node
from pong_msgs.msg import PongGameState


class PongWebSocketServer:
    """WebSocket server for handling client paddle input"""

    def __init__(self, node: Node, host: str = "0.0.0.0", port: int = 8765):
        """
        Initialize WebSocket server.

        Args:
            node: ROS 2 node for publishing paddle input
            host: Server host address
            port: Server port
        """
        self.node = node
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.paddle_input_publisher = node.create_publisher(
            PongGameState, '/pong/paddle_input', 10)

    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket client connection"""
        self.clients.add(websocket)
        self.node.get_logger().info(
            f'Client connected. Total clients: {len(self.clients)}'
        )

        try:
            async for message in websocket:
                await self.process_message(message)
        except websockets.exceptions.ConnectionClosed:
            self.node.get_logger().info('Client disconnected')
        finally:
            self.clients.discard(websocket)
            self.node.get_logger().info(
                f'Client removed. Total clients: {len(self.clients)}'
            )

    async def process_message(self, message: str):
        """Process incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'paddle_move':
                player = data.get('player', 2)
                paddle_y = data.get('paddle_y', 0.0)

                # Publish to ROS topic
                ros_msg = PongGameState()
                if player == 1:
                    ros_msg.paddle1_y = paddle_y
                    ros_msg.paddle2_y = 0.0
                else:  # player 2
                    ros_msg.paddle1_y = 0.0
                    ros_msg.paddle2_y = paddle_y

                self.paddle_input_publisher.publish(ros_msg)

        except json.JSONDecodeError:
            self.node.get_logger().warning(f'Invalid JSON message: {message}')
        except Exception as e:
            self.node.get_logger().error(f'Error processing message: {e}')

    async def start(self):
        """Start the WebSocket server"""
        async with websockets.serve(self.handle_client, self.host, self.port):
            self.node.get_logger().info(
                f'WebSocket server started on ws://{self.host}:{self.port}'
            )
            # Keep the server running
            await asyncio.Future()

    def run_in_thread(self):
        """Run the server in a separate thread"""
        import threading

        def server_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start())
            except KeyboardInterrupt:
                self.node.get_logger().info('WebSocket server stopped')
            finally:
                loop.close()

        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        return thread
