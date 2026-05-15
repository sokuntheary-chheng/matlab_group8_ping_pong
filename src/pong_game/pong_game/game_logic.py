import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState
import math

class PongGameLogic(Node):
    def __init__(self):
        super().__init__('pong_game_logic')

        # Publisher
        self.publisher = self.create_publisher(PongGameState, '/pong/game_state', 10)

        # Subscriber for paddle input
        self.subscription = self.create_subscription(
            PongGameState, '/pong/paddle_input', self.paddle_callback, 10)

        # Game state
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vel_x = 2.0
        self.ball_vel_y = 1.0
        self.paddle1_y = 0.0
        self.paddle2_y = 0.0
        self.score1 = 0
        self.score2 = 0
        self.game_status = 1

        # Arena size
        self.arena_w = 10.0
        self.arena_h = 6.0
        self.paddle_h = 1.5

        # Timer 20Hz
        self.timer = self.create_timer(0.05, self.update_game)
        self.get_logger().info('Pong Game Logic started!')

    def paddle_callback(self, msg):
        self.paddle1_y = msg.paddle1_y
        self.paddle2_y = msg.paddle2_y

    def update_game(self):
        if self.game_status != 1:
            return

        # Move ball
        self.ball_x += self.ball_vel_x * 0.05
        self.ball_y += self.ball_vel_y * 0.05

        # Bounce off top/bottom
        if abs(self.ball_y) >= self.arena_h / 2:
            self.ball_vel_y *= -1
            self.ball_y = math.copysign(self.arena_h / 2, self.ball_y)

        # Paddle collision left (paddle1)
        if self.ball_x <= -self.arena_w / 2 + 0.5:
            if abs(self.ball_y - self.paddle1_y) <= self.paddle_h / 2:
                self.ball_vel_x *= -1
                self.ball_x = -self.arena_w / 2 + 0.5
            else:
                self.score2 += 1
                self.get_logger().info(f'Player 2 scores! {self.score1}-{self.score2}')
                self.reset_ball()

        # Paddle collision right (paddle2)
        if self.ball_x >= self.arena_w / 2 - 0.5:
            if abs(self.ball_y - self.paddle2_y) <= self.paddle_h / 2:
                self.ball_vel_x *= -1
                self.ball_x = self.arena_w / 2 - 0.5
            else:
                self.score1 += 1
                self.get_logger().info(f'Player 1 scores! {self.score1}-{self.score2}')
                self.reset_ball()

        # Check win condition
        if self.score1 >= 5:
            self.game_status = 2
            self.get_logger().info('Player 1 WINS!')
        elif self.score2 >= 5:
            self.game_status = 3
            self.get_logger().info('Player 2 WINS!')

        # Publish state
        msg = PongGameState()
        msg.ball_x = self.ball_x
        msg.ball_y = self.ball_y
        msg.ball_vel_x = self.ball_vel_x
        msg.ball_vel_y = self.ball_vel_y
        msg.paddle1_y = self.paddle1_y
        msg.paddle2_y = self.paddle2_y
        msg.score_player1 = self.score1
        msg.score_player2 = self.score2
        msg.game_status = self.game_status
        self.publisher.publish(msg)

    def reset_ball(self):
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vel_x *= -1

def main(args=None):
    rclpy.init(args=args)
    node = PongGameLogic()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
