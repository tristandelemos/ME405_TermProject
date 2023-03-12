"""!@file servo.py
        This file contains the class which allows for proportional-
        integral-derivative control of the motor. The class contains
        an initializer and 5 methods: run, set_setpoint, set_Kp,
        set_Ki, and set_Kd
"""
import pyb
import utime

class Servo:

    def __init__(self,pin,timer,channel):
        self.pin = pyb.Pin(pin,pyb.Pin.OUT_PP)
        self.timer = pyb.Timer (timer,freq = 50)
        self.PWM_1 = self.timer.channel(channel,pyb.Timer.PWM,pin = self.pin)
        
    def set_pos(self,pos):
        pos = (pos/180*1.5+0.5)/20*100
        
        self.PWM_1.pulse_width_percent(pos)
        
if __name__ =='__main__':
    ser = Servo(pyb.Pin.board.PB10,2,3)
    ser.set_pos(20)
    utime.sleepms(50)
    ser.set_pos(0)