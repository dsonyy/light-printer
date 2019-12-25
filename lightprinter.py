import time
import sys
import glob
import serial
import imageio
import playsound

SERIAL_TIMEOUT = 0.1
PLAY_SOUND = False

LIGHT_TIME = 3 # s
Z_SLEEP_PER_MM = 0.19 # s / mm
X_SLEEP_PER_MM = 0.05 # s / mm
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

def modify_constants():
    global LIGHT_TIME
    global Z_SLEEP_PER_MM
    global X_SLEEP_PER_MM
    global X_STEP
    global Z_STEP

    print("##    Enter new constant (empty line to skip):")

    print("##      Pixel light time (", LIGHT_TIME, "sec ): ", end="")
    try:
        new = float(input())
        if not new >= 0: raise ValueError
        LIGHT_TIME = new
    except:
        print("ERR! Invalid input. Value did not changed.")
        return

    print("##      X axis step (", X_STEP, "sec ): ", end="")
    try:
        new = float(input())
        if not new >= 0: raise ValueError
        X_STEP = new
    except:
        print("ERR! Invalid input. Value did not changed.")
        return

    print("##      Z axis step (", Z_STEP, "sec ): ", end="")
    try:
        new = float(input())
        if not new >= 0: raise ValueError
        Z_STEP = new
    except:
        print("ERR! Invalid input. Value did not changed.")
        return

    print("##      X axis sleep per mm (", X_SLEEP_PER_MM, "sec ): ", end="")
    try:
        new = float(input())
        if not new >= 0: raise ValueError
        X_SLEEP_PER_MM = new
    except:
        print("ERR! Invalid input. Value did not changed.")
        return

    print("##      Z axis sleep per mm (", Z_SLEEP_PER_MM, "sec ): ", end="")
    try:
        new = float(input())
        if not new >= 0: raise ValueError
        Z_SLEEP_PER_MM = new
    except:
        print("ERR! Invalid input. Value did not changed.")
        return



def menu(s):
    print("##################################################")
    print("##")
    print("##    Type a letter to nagivate:")
    print("##      d - DRAW AN IMAGE")
    print("##      c - Configure COM connection")
    print("##      m - Modify constants")
    print("##      g - Live G-Code session")
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
        ch = input("> ")
        if ch in ['d', 'D']:
            pass
        elif ch in ['c', 'C']:
            pass
        elif ch in ['m', 'M']:
            modify_constants()
        elif ch in ['g', 'G']:
            pass
        elif ch in ['h', 'H']:
            pass
        else:
            print("ERR! Unknown command")
            continue
        break

    
def color_hex(color):
    c = ""
    c += color

def main():
    # Welcome screen
    s = serial.Serial()
    menu(s)


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
    
    # Start time measurement
    start = time.time()
    print("Time measurement started")

    img = img[::-1]
    for row, index in zip(img, range(len(img))):
        if index % 2:
            row = row[::-1]

        for px, x in zip(row, range(len(row))):
            if index % 2: print(index, len(row) - 1 - x, ":")
            else: print(index, x, ":")
            # Turn the light on and set its color
            if PLAY_SOUND:
                try: playsound.playsound("on.mp3")
                except: pass
            print("Turn on light --", hex(px[0])[2:].zfill(2) + hex(px[1])[2:].zfill(2) + hex(px[2])[2:].zfill(2))
            pass

            # Wait 
            time.sleep(LIGHT_TIME)


            # Turn off the light
            if PLAY_SOUND:
                try: playsound.playsound("off.mp3")
                except: pass
            print("Turn off light")
            pass

            # Move X
            if x == len(row) - 1:
                break
            gcode = "G0 X"
            if index % 2: gcode += str(-X_STEP)
            else: gcode += str(X_STEP)
            print(">>>> Sending line --", gcode)
            s.write(str.encode(gcode + "\n"))

            # Sleeping
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


try:
    main()
except KeyboardInterrupt:
    print("EOF recieved. Program stopped.")
# input("Program Finished, press any key to continue. ")