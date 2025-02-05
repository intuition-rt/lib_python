import ilo
import unittest
import time

my_ilo = None

class TestIloBluetooth(unittest.TestCase):

    def test_ilo_bluetooth(self):
        ilo.check_robot_on_bluetooth()
        time.sleep(5)
        my_ilo = ilo.robot(1)
        self.assertTrue(my_ilo.ID == 1)


if __name__ == '__main__':
    unittest.main()