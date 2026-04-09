from __future__ import annotations
from enum import IntFlag
import re


DIAGNOSTIC_COUNT = 16


class Diagnostic(IntFlag):
    IMU_INIT = 1 << 0
    IMU_WORKING = 1 << 1

    GENERAL_RECEPTION = 1 << 2

    MOTOR_1 = 1 << 3
    MOTOR_2 = 1 << 4
    MOTOR_3 = 1 << 5
    MOTOR_4 = 1 << 6

    SENSOR_COLOR_LEFT = 1 << 7
    SENSOR_COLOR_CENTER = 1 << 8
    SENSOR_COLOR_RIGHT = 1 << 9

    BRIGHTNESS = 1 << 10

    SENSOR_DISTANCE_FRONT = 1 << 11
    SENSOR_DISTANCE_RIGHT = 1 << 12
    SENSOR_DISTANCE_BACK = 1 << 13
    SENSOR_DISTANCE_LEFT = 1 << 14

    MOTOR_TASK = 1 << 15

    @classmethod
    def from_string(cls, raw_diagnostic: str) -> Diagnostic:
        # The diagnostic trame response use the following format:
        # <110s1s1s1s1s1s1s1s1s1s1s1s1s1s1s1s1>

        # where each step of the diagnostic is a boolean value prefixed with an
        # 's'

        unwrapped = "".join(re.findall(r's([01])', raw_diagnostic))
        if len(unwrapped) != DIAGNOSTIC_COUNT:
            raise ValueError

        val = sum(
            2 ** n for n, v in enumerate(unwrapped)
            if v == '1'
        )

        return cls(val)

    def print(self):
        print("--- Robot Diagnostic ---")

        for i in range(DIAGNOSTIC_COUNT):
            flag = 1 << i
            status = "ok" if self.value & flag else "ko"

            name = next((m.name for m in self.__class__ if m.value == flag), "RESERVED")
            print(f"[{i:02}] {name:<22}: {status}")
