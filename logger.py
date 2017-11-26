# Pyromania logger ver0

import datetime
import struct


INFO_STREM_ID = 0

class LogWriter:
    def __init__(self, prefix='naio', note=''):
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
        dt = datetime.datetime.now() - self.start_time
        assert dt.days == 0, dt
        assert dt.seconds < 3600, dt  # overflow not supported yet
        assert len(data) < 0x10000, len(data)  # large data blocks are not supported yet
        self.f.write(struct.pack('IHH', dt.seconds * 1000000 + dt.microseconds,
                stream_id, len(data)))
        self.f.write(data)
        self.f.flush()

    def close(self):
        self.f.close()
        self.f = None


    # context manager functions
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# vim: expandtab sw=4 ts=4
