import time
import sys
import glob
import serial
import imageio

SERIAL_TIMEOUT = 1

LIGHT_TIME = 1 # s
X_STEP = 10 # mm
Z_STEP = 10 # mm

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

    print("Available serial ports:")
    for p in ports:
        print(" ", p)

def wait_for_signal(s, signal, timeout=10) -> bool:
    print("Waiting for", signal, "signal")
    resp = b""
    for _ in range(int(timeout / SERIAL_TIMEOUT)):
        resp += s.read(100)
        if str.encode(signal) in resp:
            print("Recieved", signal, "signal")
            return True

    print("ERR! Response timeout hit")
    return False

def live_mode(s):
    print("Live mode enabled (empty line ends):")
    inpt = " "
    while inpt:
        inpt = input(": ")
        s.write(str.encode(inpt + "\n"))

def print_menu(s):
    print("##\tType a letter to nagivate:")
    print("##\t c - Configure COM connection")
    print("##\t g - Live G-Code session")
    print("##\t d - Draw picture by light")
    print("##\t h - Get some help about this project")
    print("##\t")
    if s.port:
        print("##\t", s.port)
    else:
        print("##\tNot connected")
    print("##\t")
    
def color_hex(color):
    c = ""
    c += color

def main():
    # Welcome screen
    # print("##\t")
    # print("##\tWelcome to LIGHTPRINTER software!")
    # print("##\t")
    s = serial.Serial()
    # print_menu(s)

    # Printing available serial ports
    try:
        print_serial_ports()
    except Exception as e:
        print("ERR! An error occured:", e)
        return -1

    # Estabilishing connection
    i = input("Which one to connect? ")
    try:
        s = serial.Serial(i, 115200, timeout=SERIAL_TIMEOUT)
        print("Connection estabilished")
    except Exception as e:
        print("ERR! An error occured:", e)
        return -1

    # Waiting for 'start' signal form printer
    signal = "wait"
    if not wait_for_signal(s, signal):
        print("ERR! Signal", signal, "not sent")
        return -1

    # Sending (or not) header.gcode
    try:
        header = open("header.gcode", "r")
        cnt = 1
        for line in header:
            print(">>>> Sending line", cnt, "--", line.strip())
            cnt += 1
            s.write(str.encode(line + "\n"))
            # s.flushInput()
            # wait_for_signal(s, "wait")
    except FileNotFoundError:
        print("Header not found")
    except Exception as e:
        print("ERR! An error occured:", e)
        return -1

    make_image(s)

    live_mode(s)
    
    s.close()

def make_image(s):
    # Loading image
    filename = input("Enter image filename: ")
    try:
        img = imageio.imread(filename)
    except FileNotFoundError:
        print("ERR! File not found")
        return
    except Exception as e:
        print("ERR! An error occured:", e)
    
    # Displaying image pixel colors
    print("Colors loaded:")
    for row in img:
        for px in row:
            print(hex(px[0])[2:].zfill(2), hex(px[1])[2:].zfill(2), hex(px[2])[2:].zfill(2), end=" ", sep="")
        print("")
    
    img.reverse()
    for row in img:
        if img.index(row) % 2:
            row.reverse()

        for px in row:
            # Turn the light on and set its color
            print("Turn on light --", hex(px[0])[2:].zfill(2) + hex(px[1])[2:].zfill(2) + hex(px[2])[2:].zfill(2))
            pass

            # Wait 
            time.sleep(LIGHT_TIME)

            # Turn off the light
            print("Turn off light")
            pass

            # Move X
            gcode = "G0 X" + str(X_STEP)
            print(">>>> Sending line --", gcode)
            s.write(str.encode(gcode + "\n"))
            s.flushInput()
            wait_for_signal(s, "wait")
            
        # Move Z
        gcode = "G0 Z" + str(Z_STEP)
        print(">>>> Sending line --", gcode)
        s.write(str.encode(gcode + "\n"))
        s.flushInput()
        wait_for_signal(s, "wait")
        

main()
# input("Program Finished, press any key to continue. ")