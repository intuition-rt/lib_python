import ilo

ilo.check_robot_on_serial()
ilo.check_robot_on_bluetooth()

from ilo import ilo, ConnectionType
from ilo.ilo import Robot

robot = ilo.robot("Sigma", connect_with=ConnectionType.SERIAL, debug=True)
robot2 = ilo.robot("Aqua", connect_with=ConnectionType.BLUETOOTH, debug=True)

def test_trame(robot, mtd, *args):
    m_name = mtd.__name__
    print(f"\033[34m{mtd.__name__}({', '.join(map(str, args))})\033[0m ")

    ins_mtd = getattr(robot, m_name)
    print(f"\033[32m{mtd.__name__}\033[0m:\033[0m", ins_mtd(*args))


getter_methods = [
    Robot.get_acc_motor,
    Robot.get_accessory_info,
    Robot.get_angle,
    Robot.get_battery,
    Robot.get_color_card,
    Robot.get_color_clear,
    Robot.get_color_clear_center,
    Robot.get_color_clear_left,
    Robot.get_color_clear_right,
    Robot.get_color_rgb_center,
    Robot.get_color_rgb_left,
    Robot.get_color_rgb_right,
    Robot.get_distance,
    Robot.get_distance_back,
    Robot.get_distance_front,
    Robot.get_distance_left,
    Robot.get_distance_right,
    Robot.get_first_use_date,
    Robot.get_led_color,
    Robot.get_line,
    Robot.get_line_center,
    Robot.get_line_left,
    Robot.get_line_right,
    Robot.get_line_threshold_value,
    Robot.get_manufacturing_date,
    Robot.get_name,
    Robot.get_pid,
    Robot.get_pitch,
    Robot.get_product_id,
    Robot.get_product_version,
    Robot.get_raw_imu,
    Robot.get_robot_version,
    Robot.get_roll,
    Robot.get_tempo_pos,
    Robot.get_wifi_credentials,
    Robot.get_yaw,
]

for mtd in getter_methods:
    test_trame(robot, mtd)
    test_trame(robot2, mtd)

motor_methods = [
    Robot.get_current_single_motor,
    Robot.get_motor_is_moving,
    Robot.get_single_motor_angle,
    Robot.get_single_motor_speed,
    Robot.get_temp_single_motor,
    Robot.get_torque_single_motor,
    Robot.get_volt_single_motor,
]

for motor_id in range(1, 5):
    for mtd in motor_methods:
        test_trame(robot, mtd, motor_id)
        test_trame(robot2, mtd, motor_id)
