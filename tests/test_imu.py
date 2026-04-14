import ilo
from ilo import ConnectionType

ilo.check_robot_on_bluetooth()
robot = ilo.robot("Sigma", connect_with=ConnectionType.BLUETOOTH, debug=False)

def test_imu():
    robot.reset_angle()

    while True:
        angles = robot.get_angle()
        raw = robot.get_raw_imu()

        print(f"{angles[0]:<8.2f} | {angles[1]:<8.2f} | {angles[2]:<8.2f}")

        print(f"DEBUG Raw Acc: X:{raw[0]:.2f} Y:{raw[1]:.2f} Z:{raw[2]:.2f}")
        print(f"DEBUG Raw Gyro: R:{raw[3]:.2f} P:{raw[4]:.2f} G:{raw[5]:.2f}")


if __name__ == "__main__":
    test_imu()
