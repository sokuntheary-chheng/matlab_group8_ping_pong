from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'pong_game'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sparkling',
    maintainer_email='sparkling@example.com',
    description='ROS 2 Pong Game',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'game_logic = pong_game.game_logic:main',
            'keyboard_controller = pong_game.keyboard_controller:main',
            'visualizer = pong_game.visualizer:main',
            'pygame_pong = pong_game.pygame_pong:main',
        ],
    },
)
