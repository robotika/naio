# naio
Experiments with Naio robots

## 2017 

Preparation for "Move Your Robot" contest
https://www.naio-technologies.com/Fira/en/move-your-robot/

![MYR2017](https://robotika.cz/competitions/move-your-robot/2017/world2.jpg)

The development is described in the article on
https://robotika.cz/competitions/move-your-robot/2017/

## Usage

```
python3 -h
usage: myr2017.py [-h] [--host HOST] [--port PORT] [--note NOTE] [--verbose]
                  [--video-port VIDEO_PORT] [--replay REPLAY] [--force]
                  [--test {1m,90deg,loops}]

Navigate Naio robot in "Move Your Robot" competition

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           IP address of the host
  --port PORT           port number of the robot or simulator
  --note NOTE           add run description
  --verbose             show laser output
  --video-port VIDEO_PORT
                        optional video port 5558 for simulator, default "no
                        video"
  --replay REPLAY       replay existing log file
  --force, -F           force replay even for failing output asserts
  --test {1m,90deg,loops}
                        test cases
```

