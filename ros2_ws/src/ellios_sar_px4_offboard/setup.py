from setuptools import setup

package_name = 'ellios_sar_px4_offboard'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='ELIOS-SAR PX4 Offboard Controller',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'offboard_controller = '
            'ellios_sar_px4_offboard.offboard_controller:main',
        ],
    },
)
