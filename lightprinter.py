import time
import sys
import glob
import serial

SERIAL_TIMEOUT = 0.5

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
    
def print_serial_ports() -> bool:
    try:
        ports = serial_ports()
    except Exception as e:
        print("ERR! An error occured: ", e)
        return False
    
    print("Available serial ports:")
    for p in ports:
        print(" ", p)
    return True

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

def main():
    # Printing available serial ports
    if not print_serial_ports():
        return -1

    # Estabilishing connection
    i = input("Which one to connect? ")
    try:
        s = serial.Serial(i, 115200, timeout=serial_timeout)
        print("Connection estabilished")
    except:
        print("ERR! Unable to connect with", i)
        return -1

    # Waiting for 'start' signal form printer
    signal = "wait"
    if not wait_for_signal(s, signal):
        print("ERR! Signal", signal, "not sent")
        return -1
    
    time.sleep(3)

    # Sending (or not) header.gcode
    #try:
    header = open("header.gcode", "r")
    for line in header:
        print("<<<", line)

        s.write(str.encode(line))
        # time.sleep(1)
        s.flushInput()
        wait_for_signal(s, "wait")
        
        

    #except:
    #    print("Header not found")

    # s.write(str.encode(a))
    
    
    s.close()


main()
input("Program Finished, press any key to continue. ")