import ilo

ilo.check_robot_on_bluetooth()

robot = ilo.robot("Sigma")


def distance_to_red(dist):
    brightness = 255 * (1 - dist / 600) ** 5
    return int(brightness)


while True:
    dist = robot.get_distance_front()
    red = distance_to_red(dist)
    robot.set_led_color(red, 0, 0)
