#!/usr/bin/python

"""common.py: Common utility functions for TopOSM"""

import os, time, sys
from os import path
from threading import Lock

import filelock

from env import *

__author__      = "Lars Ahlzen"
__copyright__   = "(c) Lars Ahlzen 2008-2011"
__license__     = "GPLv2"


class ErrorLog:
    lock = Lock()
    def log(self, message, exception = None):
        timestr = time.strftime('[%Y-%m-%d %H:%M:%S]')
        ErrorLog.lock.acquire()
        try:
            file = open(ERRORLOG, 'a')
            file.write("%s %s (%s)\n" % (timestr, message, str(exception)))
            file.close()
        except:
            print("Failed to write to the error log:")
            print("%s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        finally:
            ErrorLog.lock.release()        

errorLog = ErrorLog()


# global locking object for file system ops (e.g. creating directories)
fslock = filelock.FileLock('/tmp/lock.TopOSM.fslock')

def ensureDirExists(path):
    with fslock:
        if not os.path.isdir(path):
            os.makedirs(path)
