import rclpy
from rclpy.node import Node
from pong_msgs.msg import PongGameState
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Vector3

class PongVisualizer(Node):
    def __init__(self):
        super().__init__('pong_visualizer')
        self.subscription = self.create_subscription(
            PongGameState, '/pong/game_state', self.state_callback, 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/pong/markers', 10)
        self.get_logger().info('Pong Visualizer started!')

    def make_marker(self, id, x, y, sx, sy, sz, r, g, b):
        m = Marker()
        m.header.frame_id = 'map'
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns = 'pong'
        m.id = id
        m.type = Marker.CUBE
        m.action = Marker.ADD
        m.pose.position.x = float(x)
        m.pose.position.y = float(y)
        m.pose.position.z = 0.0
        m.pose.orientation.w = 1.0
        m.scale = Vector3(x=float(sx), y=float(sy), z=float(sz))
        m.color = ColorRGBA(r=float(r), g=float(g), b=float(b), a=1.0)
        return m

    def state_callback(self, msg):
        markers = MarkerArray()

        # Ball (white)
        markers.markers.append(
            self.make_marker(0, msg.ball_x, msg.ball_y, 0.3, 0.3, 0.3, 1.0, 1.0, 1.0))

        # Paddle 1 left (green)
        markers.markers.append(
            self.make_marker(1, -4.75, msg.paddle1_y, 0.3, 1.5, 0.3, 0.0, 1.0, 0.0))

        # Paddle 2 right (red)
        markers.markers.append(
            self.make_marker(2, 4.75, msg.paddle2_y, 0.3, 1.5, 0.3, 1.0, 0.0, 0.0))

        # Top wall (blue)
        markers.markers.append(
            self.make_marker(3, 0.0, 3.15, 10.0, 0.3, 0.3, 0.0, 0.0, 1.0))

        # Bottom wall (blue)
        markers.markers.append(
            self.make_marker(4, 0.0, -3.15, 10.0, 0.3, 0.3, 0.0, 0.0, 1.0))

        self.marker_pub.publish(markers)
        self.get_logger().info(
            f'Score: {msg.score_player1} - {msg.score_player2} | '
            f'Ball: ({msg.ball_x:.1f}, {msg.ball_y:.1f})',
            throttle_duration_sec=1.0)

def main(args=None):
    rclpy.init(args=args)
    node = PongVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
