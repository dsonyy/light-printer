
###############################################################################
###############################################################################
###############################################################################

SERIAL_TIMEOUT = 0.1 # s
LIGHT_TIME = 0.05 # s
Z_SLEEP_PER_MM = 0.14 # s / mm
X_SLEEP_PER_MM = 0.04 # s / mm
X_STEP = 9.5 # mm
Z_STEP = 9.5 # mm
BLACK_THRESHOLD = 0 # 0-255
DEFAULT_PORT = "/dev/ttyUSB0"

PIN_RED = 21
PIN_GREEN = 20
PIN_BLUE = 16

###############################################################################
###############################################################################
###############################################################################

import time
import sys
import serial
import imageio
import glob
from os import listdir
import pigpio

# Source: https://stackoverflow.com/a/14224477/7389107
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
    
def print_serial_ports():
    ports = serial_ports()

    print("##    Available serial ports:")
    for p in ports:
        print("##      ", p)

def wait_for_signal(s, signal, timeout=10) -> bool:
    print("Waiting for '", signal, "' signal.", sep="")
    resp = b""
    for _ in range(int(timeout / SERIAL_TIMEOUT)):
        resp += s.read(100)
        if str.encode(signal) in resp:
            print("Recieved '", signal, "' signal.", sep="")
            return True

    print("ERR! Timeout.")
    return False

def live_mode(s):
    print("Live mode enabled (empty line ends):")
    inpt = " "
    while inpt:
        inpt = input("> ")
        s.write(str.encode(inpt + "\n"))

def configure_com(port=None) -> serial.Serial:
    # Printing available serial ports
    try:
        print_serial_ports()
    except Exception as e:
        print("ERR! An error occured:", e)
        return serial.Serial()

    # Estabilishing connection
    if not port: i = input("##    Port: ")
    else: i = port
    try:
        s = serial.Serial(i, 115200, timeout=SERIAL_TIMEOUT)
        print("Connection estabilished.")
    except Exception as e:
        print("ERR! An error occured:", e)
        return serial.Serial()

    # Waiting for 'start' signal form printer
    signal = "wait"
    if not wait_for_signal(s, signal):
        print("ERR! Signal", signal, "not sent.")
        return serial.Serial()

    return s

def send_header(s):
    try:
        header = open("header.gcode", "r")
        print("Header file found. Sending it to the printer.")
        cnt = 1
        for line in header:
            print(">>>> Sending line", cnt, "--", line.strip())
            cnt += 1
            s.write(str.encode(line + "\n"))
            print("Header sent.")
    except FileNotFoundError:
        print("Header file not found.")
    except Exception as e:
        print("ERR! An error occured:", e)
        return
    s.flushInput()
    wait_for_signal(s, "wait", 10000)

def send_footer(s):
    try:
        header = open("footer.gcode", "r")
        print("Footer file found. Sending it to the printer.")
        cnt = 1
        for line in header:
            print(">>>> Sending line", cnt, "--", line.strip())
            cnt += 1
            s.write(str.encode(line + "\n"))
        print("Footer sent.")
    except FileNotFoundError:
        print("Footer file not found.")
    except Exception as e:
        print("ERR! An error occured:", e)
        return
    # s.flushInput()
    # wait_for_signal(s, "wait", 10000)

def make_image(s, gpio):
    # List available images
    print("##    Available input images:")
    files = listdir("input/")
    for inp in files:
        print("##       ", files.index(inp) + 1, ". ", inp, " ", sep="")
    print("##")
    
    # Loading image
    try:
        number = int(input("Enter image number: "))
        if number - 1 < 0: raise IndexError
        img = imageio.imread("input/" + files[number - 1])
    except FileNotFoundError:
        print("ERR! File not found.")
        return
    except (IndexError, ValueError):
        print("ERR! Invalid numer.")
        return
    except Exception as e:
        print("ERR! An error occured:", e)
        return
    
    # Displaying image pixel colors
    print("Colors loaded:")
    print("Dimensions:", len(img), "x", len(img[0]))
    for row in img:
        for px in row:
            print(hex(px[0])[2:].zfill(2), hex(px[1])[2:].zfill(2), hex(px[2])[2:].zfill(2), end=" ", sep="")
        print("")
    
    # Sending header
    send_header(s)

    # Time to start drawing
    while True:
        try:
            delay = int(input("Enter seconds to start drawing: "))
            for i in reversed(range(delay)):
                print(i + 1)
                time.sleep(1)
            print("DRAWING STARTED.")
        except ValueError:
            print("ERR! Bad input.")
            continue
        break

    # Start time measurement
    start = time.time()
    print("Time measurement started.")

    # Drawing
    img = img[::-1]
    for row, index in zip(img, range(len(img))):
        if index % 2:
            row = row[::-1]
       
        for px, x in zip(row, range(len(row))):
            if index % 2: print(index, len(row) - 1 - x, ":")
            else: print(index, x, ":")

            if px[0] <= BLACK_THRESHOLD and px[1] <= BLACK_THRESHOLD and px[2] <= BLACK_THRESHOLD:
                print("Skipping black pixel.")
            else:
                # Turn the light on and set its color
                print("Turn on the light --", hex(px[0])[2:].zfill(2) + hex(px[1])[2:].zfill(2) + hex(px[2])[2:].zfill(2))
                gpio.set_PWM_dutycycle(PIN_RED, px[0])
                gpio.set_PWM_dutycycle(PIN_GREEN, px[1])
                gpio.set_PWM_dutycycle(PIN_BLUE, px[2])

                # Wait
                time.sleep(LIGHT_TIME)

                # Turn off the light
                print("Turn off the light.")
                gpio.set_PWM_dutycycle(PIN_RED, 0)
                gpio.set_PWM_dutycycle(PIN_GREEN, 0)
                gpio.set_PWM_dutycycle(PIN_BLUE, 0)

            # Move X
            if x == len(row) - 1:
                break
            gcode = "G0 X"
            if index % 2: gcode += str(-X_STEP)
            else: gcode += str(X_STEP)
            print(">>>> Sending line --", gcode)
            s.write(str.encode(gcode + "\n"))

            # Sleeping
            if True: # not (px[0] == 0 and px[1] == 0 and px[2] == 0):
                time.sleep(X_STEP * X_SLEEP_PER_MM)
                # s.flushInput()
                # wait_for_signal(s, "wait")
            
        # Move Z
        if index == len(img) - 1:
            break
        gcode = "G0 Z" + str(Z_STEP)
        print(">>>> Sending line --", gcode)
        s.write(str.encode(gcode + "\n"))

        # Sleeping
        time.sleep(Z_STEP * Z_SLEEP_PER_MM)
        # s.flushInput()
        # wait_for_signal(s, "wait")


    end = time.time()
    print("Operation time:", end - start, "seconds")
    print("Total pixels:", len(img) * len(img[0]))
    print("Average time for single pixel:", (end - start) / (len(img) * len(img[0])), "seconds")

    send_footer(s)

def main():
    s = configure_com()
    print("RGB Mode. Pin red:", PIN_RED, ", pin green:", PIN_GREEN, ", pin blue:", PIN_BLUE)
    print("Initializing GPIOs")
    gpio = pigpio.pi()
    gpio.set_PWM_dutycycle(PIN_RED, 0)
    gpio.set_PWM_dutycycle(PIN_GREEN, 0)
    gpio.set_PWM_dutycycle(PIN_BLUE, 0)

    while True:
        print("##################################################")
        print("##")
        print("##    Type a letter to nagivate:")
        print("##      c - Configure COM connection")
        print("##      d - DRAW AN IMAGE")
        print("##      h - Get some help about this project")
        print("##")
        if s.port: print("##    Port:", s.port)
        else: print("##    Port:                     Not connected")
        print("##")
        print("##    Pixel light time:        ", LIGHT_TIME, "sec")
        print("##    X axis step:             ", X_STEP, "mm")
        print("##    Z axis step:             ", Z_STEP, "mm")
        print("##    X axis sleep per mm:     ", X_SLEEP_PER_MM, "sec/mm")
        print("##    Z axis sleep per mm:     ", Z_SLEEP_PER_MM, "sec/mm")
        print("##")

        while True:
            ch = input("> ").strip()
            if ch in ['d', 'D']:
                if not s.port:
                    print("ERR! COM port not connected.")
                    continue
                try:
                    make_image(s, gpio)
                except KeyboardInterrupt:
                    print("Operation cancelled.")

            elif ch in ['c', 'C']:
                s = configure_com()

            elif ch in ['g', 'G']:
                if not s.port:
                    print("ERR! COM port not connected.")
                    continue
                live_mode(s)

            elif ch in ['h', 'H']:
                continue

            else:
                print("ERR! Unknown command")
                continue
            break
    
    s.close()

try:
    main()
except KeyboardInterrupt:
    print("EOF recieved. Program stopped.")

# input("Program Finished, press any key to continue. ")
