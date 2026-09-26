from setuptools import setup

package_name = 'ellios_sar_px4_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'px4_bridge = ellios_sar_px4_bridge.px4_bridge:main',
        ],
    },
)
