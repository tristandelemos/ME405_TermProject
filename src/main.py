# Created by Tristan de Lemos, Trenten Spicer, and Rees Verleur
#
# main file for Turret Term Project


import utime
import cotask
import task_share
import gc
from machine import Pin, I2C
from encoder_driver import EncoderDriver
from motor_driver import MotorDriver
from pro_control import ProControl
from mlx90640 import MLX90640
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern

S0_INIT = 0
S1_TAKE_PICTURE = 1
S2_MOVE_MOTORS = 2
S3_SHOOT = 3
S4_PAUSE = 4


def initialize():
    pass


def take_picture(camera):
    while True:
        try:
            # Get and image and see how long it takes to grab that image
            print("Click.", end='')
            begintime = time.ticks_ms()
            image = camera.get_image()
            print(f" {time.ticks_diff(time.ticks_ms(), begintime)} ms")

            # Can show image.v_ir, image.alpha, or image.buf; image.v_ir best?
            # Display pixellated grayscale or numbers in CSV format; the CSV
            # could also be written to a file. Spreadsheets, Matlab(tm), or
            # CPython can read CSV and make a decent false-color heat plot.
            cleared_image = [];
            show_image = False
            show_csv = False
            if show_image:
                camera.ascii_image(image.buf)
            elif show_csv:
                for line in camera.get_csv(image.v_ir, limits=(0, 99)):
                    cleared_image.append(line)
                    print(line)
            else:
                camera.ascii_art(image.v_ir)
                
                for line in camera.get_csv(image.v_ir, limits=(0, 99)):
                    cleared_image.append(line)
                    time.sleep_ms(1)
                    
            # time.sleep_ms(5000)
            print()
            
            cleared_image.reverse()
            for line in cleared_image:
                linelist = line.split(",")
                newline = ""
                for i in range(len(linelist)):
                    #print(f"line[i]: {line[i]}")
                    if (int(linelist[i]) < 40):
                        linelist[i] = "0"
                        newline += "--"
                    elif (int(linelist[i]) < 50):
                        newline += "++"
                    else:
                        newline += "&&"
                        
                # newline = ",".join(linelist)
                print(newline)                
            
            time.sleep_ms(5000)

        except KeyboardInterrupt:
            break




def main():
    camera = 0
    
    state = S0_INIT
    
    while(True):
        
        try:
            if(state == S0_INIT):
                
                
                state = S1_TAKE_PICTURE
            
            
            # Take picture and find warmest area to shoot at
            if(state == S1_TAKE_PICTURE):
                take_picture(camera)
        
                state = S2_MOVE_MOTORS
        
            # Move motors to desired angles
            if(state == S2_MOVE_MOTORS):
            
                state = S3_SHOOT
            
            
            # activate servo to shoot
            if(state == S3_SHOOT):
    
                state = S4_PAUSE
       
            # pause to allow for reloading
            if(state == S4_PAUSE):
                
                utime.sleep(5)
                
                state = S1_TAKE_PICTURE
       
        except KeyboardInterrupt:
            break 
    
if __name__ == "__main__":
    """!@brief This script creates instances of all the required modules and
            calls the test program in main()
        @details The classes have to be instantiated here outside of functions
            so that their values can be accessed and changed by any function.
    """
    gc.collect()
    # Initialize uart communication
    u2 = pyb.UART(2, baudrate=115200, timeout = 65383)
    # Initialize encoder objects
    enc_1 = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    enc_2 = EncoderDriver(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    # Initialize motor objects
    motor_1 = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    motor_2 = MotorDriver (pyb.Pin.board.PC1,pyb.Pin.board.PA0,pyb.Pin.board.PA1,5)
    # Initialize proportional controllers with default values
    con_1 = ProControl()
    con_2 = ProControl()
    # Intitialize camera
    try:
        from pyb import info

    # Oops, it's not an STM32; assume generic machine.I2C for ESP32 and others
    except ImportError:
        # For ESP32 38-pin cheapo board from NodeMCU, KeeYees, etc.
        i2c_bus = I2C(1, scl=Pin(22), sda=Pin(21))

    # OK, we do have an STM32, so just use the default pin assignments for I2C1
    else:
        i2c_bus = I2C(1)

    
    
    i2c_address = 0x33
    scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
    print(f"I2C Scan: {scanhex}")
    gc.collect()
    # Create the camera object and set it up in default mode
    camera = MLX_Cam(i2c_bus)