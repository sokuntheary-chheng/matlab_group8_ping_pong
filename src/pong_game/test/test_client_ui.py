import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Provide lightweight stubs for ROS-specific imports so the UI module can be tested.
rclpy_stub = types.ModuleType('rclpy')
rclpy_stub.init = lambda *args, **kwargs: None
rclpy_stub.shutdown = lambda *args, **kwargs: None
rclpy_stub.spin = lambda *args, **kwargs: None
node_module = types.ModuleType('rclpy.node')
class DummyNode:
    def __init__(self, *args, **kwargs):
        pass
    def destroy_node(self):
        return None
node_module.Node = DummyNode
sys.modules.setdefault('rclpy', rclpy_stub)
sys.modules.setdefault('rclpy.node', node_module)

pong_msgs_module = types.ModuleType('pong_msgs')
pong_msgs_msg_module = types.ModuleType('pong_msgs.msg')
class DummyMessage:
    pass
pong_msgs_msg_module.PongGameState = DummyMessage
pong_msgs_msg_module.PongScore = DummyMessage
sys.modules.setdefault('pong_msgs', pong_msgs_module)
sys.modules.setdefault('pong_msgs.msg', pong_msgs_msg_module)

from pong_game import pong_client


def test_client_draw_game_uses_host_renderer(monkeypatch):
    called = {}

    def fake_draw_game(screen, node, fonts, mode, particles, trail, settings_dict, clock=None):
        called['screen'] = screen
        called['node'] = node
        called['fonts'] = fonts
        called['mode'] = mode
        called['particles'] = particles
        called['trail'] = trail
        called['settings_dict'] = settings_dict
        called['clock'] = clock

    monkeypatch.setattr(pong_client.host_ui, 'draw_game', fake_draw_game)

    screen = object()
    node = types.SimpleNamespace()
    fonts = {'big': object()}
    particles = []
    trail = []
    settings_dict = {}

    pong_client.draw_game(screen, node, fonts, particles, trail, settings_dict, None)

    assert called['screen'] is screen
    assert called['node'] is node
    assert called['fonts'] is fonts
    assert called['mode'] == 3
    assert called['particles'] == particles
    assert called['trail'] == trail
    assert called['settings_dict'] is settings_dict
    assert called['clock'] is None


def test_pygame_pong_client_update_game():
    from pong_game import pygame_pong
    node = types.SimpleNamespace(
        ball_vx=2.0, ball_vy=1.0, my_paddle_y=0.0, limit=2.25,
        paddle2_y=0.0, speed_mult=1.0, countdown_active=False, _network_role='CLIENT'
    )
    pygame_pong.update_game(node, set(), mode=3, sounds={}, particles=[], trail=[], settings_dict={}, dt=0.016)
    assert hasattr(node, 'my_paddle_y')

