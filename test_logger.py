import unittest
import os
import time

from logger import *


class LoggerTest(unittest.TestCase):
    
    def test_writer_prefix(self):
        log = LogWriter(prefix='tmp')
        assert log.filename.startswith('tmp'), log.filename
        log.close()
        os.remove(log.filename)

    def test_context_manager(self):
        with LogWriter(prefix='tmp', note='1st test') as log:
            assert log.filename.startswith('tmp'), log.filename
            filename = log.filename
            log.write(10, b'\x01\x02\x02\x04')
            time.sleep(0.01)
            log.write(10, b'\x05\x06\x07\x08')
        os.remove(log.filename)

# vim: expandtab sw=4 ts=4
