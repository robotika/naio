"""
  Play recorded video
  usage:
     python play_video.py <log file>
"""

import sys
import struct
import zlib

from logger import LogReader, LogEnd


VIDEO_STREAM = 3
WRAP_SIZE = 6 + 1 + 4 + 4  # NAIO01, type, size + CRC32


def play_video(filename):
    with LogReader(filename) as log:
        buf = b''
        num_images = 0
        while True:
            try:
                data = log.read(VIDEO_STREAM)[2]
            except LogEnd:
                break
            buf += zlib.decompress(data)
            if len(buf) > 10:
                prefix = buf[:6]
                assert prefix == b'NAIO01', prefix
                size = struct.unpack_from('>I', buf, 6+1)[0]
                if len(buf) >= size + WRAP_SIZE:
                    image = buf[:size + WRAP_SIZE]
                    print('image', len(image))
                    image = image[11+5:-4]  # remove header and CRC32
                    assert len(image) == 752*480*2, len(image)
                    f = open('image_%03d.pgm' % num_images, 'wb')
                    f.write(b'P5\n752 960\n255\n')
                    f.write(image)
                    f.close()
                    num_images += 1
                    buf = buf[size + WRAP_SIZE:]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(-1)
    play_video(sys.argv[1])

# vim: expandtab sw=4 ts=4
