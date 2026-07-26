import os
os.environ.setdefault('RMW_FASTRTPS_USE_SHM', '0')
os.environ.setdefault('RMW_FASTRTPS_USE_SHARED_MEMORY', '0')
import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState
import sys
import tty
import termios
import threading


def _configure_ros_transport():
    os.environ.setdefault('RMW_FASTRTPS_USE_SHM', '0')
    os.environ.setdefault('RMW_FASTRTPS_USE_SHARED_MEMORY', '0')

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
        self._running = True

    def read_keyboard(self):
        """Read keyboard input and update paddle positions."""
        if not sys.stdin.isatty():
            self.get_logger().warning('Not running in terminal — keyboard input not available')
            return
            
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while self._running:
                try:
                    ch = os.read(fd, 1)
                    if not ch:
                        break
                    if ch == b'w':
                        self.paddle1_y = min(self.paddle1_y + self.paddle_speed, self.limit)
                        self.get_logger().info(f'P1 up: {self.paddle1_y:.2f}', throttle_duration_sec=0.1)
                    elif ch == b's':
                        self.paddle1_y = max(self.paddle1_y - self.paddle_speed, -self.limit)
                        self.get_logger().info(f'P1 down: {self.paddle1_y:.2f}', throttle_duration_sec=0.1)
                    elif ch == b'\x1b':
                        ch2 = os.read(fd, 1)
                        if ch2:
                            ch3 = os.read(fd, 1)
                            if ch2 == b'[' and ch3 == b'A':
                                self.paddle2_y = min(self.paddle2_y + self.paddle_speed, self.limit)
                                self.get_logger().info(f'P2 up: {self.paddle2_y:.2f}', throttle_duration_sec=0.1)
                            elif ch2 == b'[' and ch3 == b'B':
                                self.paddle2_y = max(self.paddle2_y - self.paddle_speed, -self.limit)
                                self.get_logger().info(f'P2 down: {self.paddle2_y:.2f}', throttle_duration_sec=0.1)
                    elif ch == b'q':
                        self.get_logger().info('Quit command received')
                        break
                except (OSError, IOError):
                    break
        except Exception as e:
            self.get_logger().error(f'Keyboard read error: {e}')
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            except:
                pass
            self._running = False

    def publish_paddles(self):
        """Publish paddle positions as game state message."""
        msg = PongGameState()
        msg.paddle1_y = self.paddle1_y
        msg.paddle2_y = self.paddle2_y
        msg.ball_x = 0.0
        msg.ball_y = 0.0
        msg.ball_vel_x = 0.0
        msg.ball_vel_y = 0.0
        msg.score_player1 = 0
        msg.score_player2 = 0
        msg.game_status = 0
        self.publisher.publish(msg)

def main(args=None):
    _configure_ros_transport()
    rclpy.init(args=args)
    node = KeyboardController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._running = False
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
