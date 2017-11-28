# Pyromania logger ver0

import datetime
import struct
from threading import Lock


INFO_STREM_ID = 0

class LogEnd(Exception):
  pass


class LogWriter:
    def __init__(self, prefix='naio', note=''):
        self.lock = Lock()
        self.start_time = datetime.datetime.now()
        self.filename = prefix + self.start_time.strftime("%y%m%d_%H%M%S.log")
        self.f = open(self.filename, 'wb')
        self.f.write(b'Pyr\x00')
        
        t = self.start_time
        self.f.write(struct.pack('HBBBBBI', t.year, t.month, t.day,
                t.hour, t.minute, t.second, t.microsecond))
        self.f.flush()
        if len(note) > 0:
            self.write(stream_id=INFO_STREM_ID, data=bytes(note, encoding='utf-8'))

    def write(self, stream_id, data):
        self.lock.acquire()
        dt = datetime.datetime.now() - self.start_time
        assert dt.days == 0, dt
        assert dt.seconds < 3600, dt  # overflow not supported yet
        assert len(data) < 0x10000, len(data)  # large data blocks are not supported yet
        self.f.write(struct.pack('IHH', dt.seconds * 1000000 + dt.microseconds,
                stream_id, len(data)))
        self.f.write(data)
        self.f.flush()
        self.lock.release()
        return dt

    def close(self):
        self.f.close()
        self.f = None


    # context manager functions
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class LogReader:
    def __init__(self, filename):
        self.filename = filename
        self.f = open(self.filename, 'rb')
        data = self.f.read(4)
        assert data == b'Pyr\x00', data
        
        data = self.f.read(12)
        self.start_time = datetime.datetime(*struct.unpack('HBBBBBI', data))

    def read(self, only_stream_id=None):
        "return (time, stream, data)"
        while True:
            header = self.f.read(8)
            if len(header) < 8:
                raise LogEnd()
            microseconds, stream_id, size = struct.unpack('IHH', header)
            dt = datetime.timedelta(microseconds=microseconds)
            data = self.f.read(size)
            if only_stream_id is None or only_stream_id == stream_id:
                return dt, stream_id, data

    def close(self):
        self.f.close()
        self.f = None


    # context manager functions
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# vim: expandtab sw=4 ts=4
