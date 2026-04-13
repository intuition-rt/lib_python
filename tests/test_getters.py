import ilo

ilo.check_robot_on_bluetooth()

from ilo import ConnectionType

robot = ilo.robot("Sigma", connect_with=ConnectionType.BLUETOOTH, debug=True)

def test_trame(mtd, *args):
    print(f"\033[34m{mtd.__name__}({', '.join(map(str, args))})\033[0m ")
    print(f"\033[32m{mtd.__name__}\033[0m:\033[0m", mtd(*args))


getter_methods = [
    robot.get_acc_motor,
    robot.get_accessory_info,
    robot.get_angle,
    robot.get_battery,
    robot.get_color_card,
    robot.get_color_clear,
    robot.get_color_clear_center,
    robot.get_color_clear_left,
    robot.get_color_clear_right,
    robot.get_color_rgb_center,
    robot.get_color_rgb_left,
    robot.get_color_rgb_right,
    robot.get_distance,
    robot.get_distance_back,
    robot.get_distance_front,
    robot.get_distance_left,
    robot.get_distance_right,
    robot.get_first_use_date,
    robot.get_led_color,
    robot.get_line,
    robot.get_line_center,
    robot.get_line_left,
    robot.get_line_right,
    robot.get_line_threshold_value,
    robot.get_manufacturing_date,
    robot.get_name,
    robot.get_pid,
    robot.get_pitch,
    robot.get_product_id,
    robot.get_product_version,
    robot.get_raw_imu,
    robot.get_robot_version,
    robot.get_roll,
    robot.get_tempo_pos,
    robot.get_yaw,
]

for mtd in getter_methods:
    test_trame(mtd)

motor_methods = [
    robot.get_current_single_motor,
    robot.get_motor_is_moving,
    robot.get_single_motor_angle,
    robot.get_single_motor_speed,
    robot.get_temp_single_motor,
    robot.get_torque_single_motor,
    robot.get_volt_single_motor,
]

for motor_id in range(1, 5):
    for mtd in motor_methods:
        test_trame(mtd, motor_id)
