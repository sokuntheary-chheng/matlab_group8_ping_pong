import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState
import sys
import os
import tty
import termios
import threading

class KeyboardController(Node):
    def __init__(self):
        super().__init__('keyboard_controller')
        self.publisher = self.create_publisher(PongGameState, '/pong/paddle_input', 10)
        self.paddle1_y = 0.0
        self.paddle2_y = 0.0
        self.paddle_speed = 0.3
        self.limit = 2.25
        self.timer = self.create_timer(0.05, self.publish_paddles)
        self.get_logger().info('Keyboard Controller started!')
        self.get_logger().info('Player 1: W/S | Player 2: Arrow Up/Down | Q: Quit')
        self.thread = threading.Thread(target=self.read_keyboard, daemon=True)
        self.thread.start()

    def read_keyboard(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = os.read(fd, 1)
                if ch == b'w':
                    self.paddle1_y = min(self.paddle1_y + self.paddle_speed, self.limit)
                    self.get_logger().info(f'P1 up: {self.paddle1_y:.2f}')
                elif ch == b's':
                    self.paddle1_y = max(self.paddle1_y - self.paddle_speed, -self.limit)
                    self.get_logger().info(f'P1 down: {self.paddle1_y:.2f}')
                elif ch == b'\x1b':
                    ch2 = os.read(fd, 1)
                    ch3 = os.read(fd, 1)
                    if ch2 == b'[' and ch3 == b'A':
                        self.paddle2_y = min(self.paddle2_y + self.paddle_speed, self.limit)
                        self.get_logger().info(f'P2 up: {self.paddle2_y:.2f}')
                    elif ch2 == b'[' and ch3 == b'B':
                        self.paddle2_y = max(self.paddle2_y - self.paddle_speed, -self.limit)
                        self.get_logger().info(f'P2 down: {self.paddle2_y:.2f}')
                elif ch == b'q':
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def publish_paddles(self):
        msg = PongGameState()
        msg.paddle1_y = self.paddle1_y
        msg.paddle2_y = self.paddle2_y
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
