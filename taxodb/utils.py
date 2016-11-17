from __future__ import print_function
import sys
from time import time


class Utils(object):
    """Utils class"""

    VERBOSE = False
    timer_start = timer_stop = 0.0

    @staticmethod
    def elapsed_time():
        """
        Get the elapsed time between start and stop timer.

        Stop timer call is not required. If not set, it is automatically called
        as soon as the method is called

        :return: Elapsed time
        :rtype: float
        :raises SystemExit: If Utils.timer_start is not defined
        """
        if Utils.timer_start:
            if not Utils.timer_stop:
                Utils.stop_timer()
            etime = Utils.timer_stop - Utils.timer_start
            Utils.reset_timer()
            return etime
        return 0.0

    @staticmethod
    def error(msg):
        """
        Print error message and exit with status 1

        :param msg: Error message to print
        :type msg: str
        """
        if msg == "":
            msg = "No error message"
        print("[ERROR] %s" % str(msg), file=sys.stderr)
        sys.exit(1)

    @staticmethod
    def get_object_size(obj, name):
        """
        Get the memory footprint of an object

        :param obj: Python object to get size from
        :type obj: object
        :param name: Named object
        :type name: str
        :return: size of object
        :rtype: int
        """
        Utils.verbose("Size of %s: %s" % (name, humanfriendly.format_size(asizeof.asizeof(obj), binary=True)))

    @staticmethod
    def reset_timer():
        """Reset to *0.0* :py:func:`timer_start` and :py:func:`timer_stop` for a new :py:func:`elapsed_time()` count"""
        Utils.timer_start = 0.0
        Utils.timer_stop = 0.0

    @staticmethod
    def start_timer():
        """Set current time at function call"""
        Utils.timer_start = time()

    @staticmethod
    def stop_timer():
        """Set current time at function call"""
        Utils.timer_stop = time()

    @staticmethod
    def verbose(msg):
        """
        Prints verbose message if Utils.verbose is True
        :param msg: Verbose message to print
        :type msg: str
        """
        if msg == "":
            msg = "No verbose message"
        if Utils.VERBOSE:
            print("[VERBOSE] %s" % str(msg))

    @staticmethod
    def warn(msg):
        """
        Prints warning message
        :param msg: Warning message to print
        :type msg: str
        :return:
        """
        if msg == "":
            msg = "No warning message"
        print("[WARNING] %s" % str(msg), file=sys.stderr)
