"""
  Use standard I/O as wrapper for Robot communication
  usage:
      python3 ./myr2017.py python3 ./naiorobot.py --port 5559
"""

import sys
import subprocess


class Robot(object):
    def __init__(self, inp, out):
        self.inp = inp
        self.out = out


def main(args):
    print(args)
    subprocess.run(args)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(-2)
    main(sys.argv[1:])

# vim: expandtab sw=4 ts=4
