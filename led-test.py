import pigpio

pi = pigpio.pi()
RED = 21
GREEN = 20
BLUE = 16

pi.set_PWM_dutycycle(BLUE, 255)
while True:
    for i in range(256):
            pi.set_PWM_dutycycle(RED, i)

    for i in reversed(range(256)):
            pi.set_PWM_dutycycle(BLUE, i)

    for i in range(256):
            pi.set_PWM_dutycycle(GREEN, i)

    for i in reversed(range(256)):
            pi.set_PWM_dutycycle(RED, i)
            
    for i in range(256):
            pi.set_PWM_dutycycle(BLUE, i)
            
    for i in reversed(range(256)):
            pi.set_PWM_dutycycle(GREEN, i)

