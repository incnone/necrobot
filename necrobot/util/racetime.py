"""
Given a time string, returns the time in total hundredths of a second, or -1 on failure.
Allowable string formats:
 [m]m:ss.hh
 [m]m:ss:hh
 [m]m:ss
"""

import unittest


def from_str(time_str):
    args = time_str.split(':')

    # mm:ss(.xx)
    if len(args) == 2:
        args_2 = args[1].split('.')

        # mm:ss
        if len(args_2) == 1 and len(args_2[0]) == 2:
            try:
                t_min = int(args[0])
                t_sec = int(args_2[0])
                return 6000*t_min + 100*t_sec
            except ValueError:
                return -1

        # mm:ss.xx
        elif len(args_2) == 2 and len(args_2[0]) == 2 and len(args_2[1]) == 2:
            try:
                t_min = int(args[0])
                t_sec = int(args_2[0])
                t_hun = int(args_2[1])
                return 6000*t_min + 100*t_sec + t_hun
            except ValueError:
                return -1

    # hh:mm:ss(.xx)
    elif len(args) == 3 and len(args[1]) == 2:
        args_2 = args[2].split('.')

        # hh:mm:ss
        if len(args_2) == 1 and len(args_2[0]) == 2:
            try:
                t_hr = int(args[0])
                t_min = int(args[1])
                t_sec = int(args[2])
                return 360000*t_hr + 6000*t_min + 100*t_sec
            except ValueError:
                return -1

        # hh:mm:ss.xx
        elif len(args_2) == 2 and len(args_2[0]) == 2 and len(args_2[1]) == 2:  # hh:mm:ss.xx
            try:
                t_hr = int(args[0])
                t_min = int(args[1])
                t_sec = int(args_2[0])
                t_hun = int(args_2[1])
                return 360000*t_hr + 6000*t_min + 100*t_sec + t_hun
            except ValueError:
                return -1

    return -1


def to_str(time_hund):          # time_hund in total hundredths of second; returns a string in the form [m]:ss.hh
    hours = int(int(time_hund) // int(360000))
    minutes = int(int(time_hund) // int(6000) - int(60)*hours)
    seconds = int(int(time_hund) // int(100) - 3600*hours - int(60)*minutes)
    hundredths = int(int(time_hund) - 100*seconds - 6000*minutes - 360000*hours)

    if hours == 0:
        return str(minutes) + ':' + str(seconds).zfill(2) + '.' + str(hundredths).zfill(2)
    else:
        return str(hours) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2) + '.' + str(hundredths).zfill(2)


class TestRaceTime(unittest.TestCase):
    def test_from_str(self):
        assert from_str('10:11.12') == 61112
        assert from_str('10:11') == 61100
        assert from_str('11') == -1
        assert from_str('10:11:12') == 3667200
        assert from_str('10:11:12.13') == 3667213

    def test_to_str(self):
        assert to_str(61112) == '10:11.12'
        assert to_str(55112) == '9:11.12'
        assert to_str(61100) == '10:11.00'
        assert to_str(3667200) == '10:11:12.00'
        assert to_str(3307200) == '9:11:12.00'
        assert to_str(60900) == '10:09.00'
        assert to_str(3667213) == '10:11:12.13'
