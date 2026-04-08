from ilo import ConnectionType
from ilo.discovery import find_in_candidates, check_robot_on_wifi
from ilo.ilo import Robot

import time


TEST_TRAME_S = (
    "<0h50z/30/611i1/611i2/611i3/611i4/621i1/621i2/621i3/621i4/63i1/63i2/63i3/63i4/64i1/64i2/64i3/64i4/>"
)


last_time = time.time()
last_x = 0


class TestRobot(Robot):
    counter = 0

    def _update_state(self, code: str, v: dict, raw: str) -> bool:
        r = super()._update_state(code, v, raw)

        if code == "0":
            self.counter += 1

        return r


check_robot_on_wifi(ap_mode=False, timeout=3)

candidate = find_in_candidates("TPLK3", use_connection_type=ConnectionType.WIFI)
assert candidate is not None

robot = TestRobot(candidate, debug=False)
robot._send_msg(TEST_TRAME_S)

while True:
    current_time = time.time()
    elapsed = current_time - last_time

    if elapsed >= 1.0:
        current_x = robot.counter
        updates_this_second = current_x - last_x
        actual_hz = updates_this_second / elapsed

        print(f"[{robot._hostname}] Frequency: {actual_hz:.2f} updates/s (Total: {current_x})")

        last_x = current_x
        last_time = current_time
