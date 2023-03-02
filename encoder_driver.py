"""!@file encoder_driver.py
        This file contains a class which allows for interaction with
        a quadrature encoder. The class contains an initializer and 3
        methods: read, zero, and update
        
        The class allows for reading of the timer attached to the
        encoder, as well as reading the absolute displacement of the
        motor accounting for over/underflow using the update method.
"""
import utime
import pyb
class EncoderDriver:
    """!
    @brief	Reads and updates the position of an encoder
    @details	The class sets up an encoder as in Lab 0 and
                reads position values from it using the read
                method. The update method takes the current
                position and the last read value and returns the 
                new absolute position accounting for over/underflow
                and direction
    """
    def __init__ (self,en_pin1, en_pin2, timer):
        """!
        @brief	Sets up the encoder class
        @details	Uses the two specified encoder pins in ENC_AB mode
                    to control the value of the specified timer
        @param	en_pin1 The first encoder pin
        @param	en_pin2 The second encoder pin
        @param	timer the timer channel associated with the encoder pins 
                specified
        """
        self.en_pin1 = pyb.Pin (en_pin1, pyb.Pin.IN)
        self.en_pin2 = pyb.Pin (en_pin2, pyb.Pin.IN)
        self.timer = pyb.Timer(timer,prescaler=0,period=0xFFFF)
        self.ch1 = self.timer.channel (1, pyb.Timer.ENC_AB, pin = self.en_pin1)
        self.ch2 = self.timer.channel (2, pyb.Timer.ENC_AB, pin = self.en_pin2)
        self.pos = 0
    
    def read(self):
        """!
        @brief	Reads the position of the encoder
        @details	Reads the value of the timer hooked to the encoder and
                    returns the current timer value
        """
        return self.timer.counter()
    
    def zero(self):
        """!
        @brief	Sets the position to zero
        @details	Zeros the timer and position for the encoder
        """
        # zero out the counter
        self.timer.counter(zero)
        self.pos = 0
    def update(self,last_read,last_pos):
        """!
        @brief	Updates the position and read values for the encoder
        @details	Takes in the last read and position values,
                    calculates the delta, and updates the position value
                    the method accounts for over/underflow and tracks absolute
                    position as a signed integer
        @param	last_read The last read value (actual timer channel)
        @param	last_pos The last absolute position value
        """
        # calculate absolute position
        curr_read = self.timer.counter()
        delta = curr_read-last_read
        if delta>32768:
            delta-=65536
        if delta<-32768:
            delta+=65536
        self.pos = last_pos+delta
        return curr_read,self.pos
    
if __name__=='__main__':
    enc = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    pos = 0
    read = enc.read()
    print("read =",read)
    while True:
        read,pos = enc.update(read,pos)
        print("read =",read)
        print("pos =",pos)
        utime.sleep_ms(100)
    
    
    
    
    
    
#pinB6 = pyb.Pin (pyb.Pin.board.PB6, pyb.Pin.IN)					# set up pin B6/B7 to read encoder A/B
#pinB7 = pyb.Pin (pyb.Pin.board.PB7, pyb.Pin.IN)
#tim4 = pyb.Timer(4,prescaler = 0,period = 0xFFFF)				# set up timer tied to encoder
#t4_ch1 = tim4.channel (1, pyb.Timer.ENC_AB, pin = pinB6)		# count up timer on each encoder pulse
#t4_ch2 = tim4.channel (2, pyb.Timer.ENC_AB, pin = pinB7)
        
        
