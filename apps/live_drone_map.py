import sys
import os
import time
import matplotlib.pyplot as plt

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    ),
)

from src.simulation.drone_simulator import (
    DroneSimulator,
)

from src.simulation.lidar_simulator import (
    LidarSimulator,
    TunnelEnvironment,
)

from src.mapping.occupancy_map import (
    OccupancyGrid,
)

from src.visualization.live_map import (
    LiveMapVisualizer,
)


def main(interactive: bool = True):

    print("Starting ELIOS-SAR live map simulation...")

    # 1. Create tunnel environment
    environment = TunnelEnvironment(
        min_x=-4.0,
        max_x=4.0,
        min_y=-3.0,
        max_y=3.0,
    )

    # 2. Create drone simulator
    drone = DroneSimulator()

    drone.connect()
    drone.arm()
    drone.takeoff(altitude=1.0)
    drone.move(x=-2.5, y=0.0)

    # 3. Create LiDAR simulator
    lidar = LidarSimulator()

    # 4. Create occupancy map
    occupancy_grid = OccupancyGrid(
        width=100,
        height=100,
        resolution=0.1,
    )

    # 5. Create visualizer
    visualizer = LiveMapVisualizer(
        occupancy_grid
    )

    # 6. Simulation loop
    total_steps = 40 if not interactive else 80

    try:
        for step in range(total_steps):

            target_x = -2.5 + step * (5.0 / total_steps)

            drone.move(
                x=target_x,
                y=0.0,
            )

            state = drone.get_state()

            drone_x = state.x
            drone_y = state.y
            drone_yaw = state.yaw

            # LiDAR scan
            measurements = lidar.scan(
                drone_x=drone_x,
                drone_y=drone_y,
                drone_yaw=drone_yaw,
                environment=environment,
            )

            # Update occupancy grid
            occupancy_grid.update_scan(
                robot_x=drone_x,
                robot_y=drone_y,
                measurements=measurements,
            )

            # Update visualization
            visualizer.update(
                drone_x=drone_x,
                drone_y=drone_y,
            )

            print(
                f"Drone: "
                f"x={drone_x:.2f} "
                f"y={drone_y:.2f} "
                f"| LiDAR rays={len(measurements)} "
                f"| Battery={state.battery:.1f}%"
            )

            if interactive:
                plt.pause(0.03)
                time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")

    finally:
        drone.hover()
        drone.land()
        drone.disarm()
        drone.disconnect()

        if interactive:
            print("Simulation complete. Showing final map window...")
            visualizer.show()
        else:
            visualizer.close()


if __name__ == "__main__":
    is_interactive = "--test" not in sys.argv and "--no-gui" not in sys.argv
    main(interactive=is_interactive)
