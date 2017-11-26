import unittest
import os
import time

from logger import *


class LoggerTest(unittest.TestCase):
    
    def test_writer_prefix(self):
        log = LogWriter(prefix='tmp')
        self.assertTrue(log.filename.startswith('tmp'))
        log.close()
        os.remove(log.filename)

    def test_context_manager(self):
        with LogWriter(prefix='tmpp', note='1st test') as log:
            self.assertTrue(log.filename.startswith('tmpp'))
            filename = log.filename
            start_time = log.start_time
            log.write(10, b'\x01\x02\x02\x04')
            time.sleep(0.01)
            log.write(10, b'\x05\x06\x07\x08')
        
        with LogReader(filename) as log:
            self.assertEqual(start_time, log.start_time)

            __, stream_id, data = log.read()
            self.assertEqual(INFO_STREM_ID, stream_id)

            t, stream_id, data = log.read()
            self.assertEqual(stream_id, 10)
            self.assertEqual(data, b'\x01\x02\x02\x04')

            t, stream_id, data = log.read()
            self.assertTrue(t.microseconds > 100)
            
            with self.assertRaises(LogEnd):
                __ = log.read()

        with LogReader(filename) as log:
            t, stream_id, data = log.read(only_stream_id=10)
            self.assertEqual(stream_id, 10)
            self.assertEqual(data, b'\x01\x02\x02\x04')

        os.remove(log.filename)

# vim: expandtab sw=4 ts=4
