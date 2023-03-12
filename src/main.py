# Created by Tristan de Lemos, Trenten Spicer, and Rees Verleur
#
# main file for Turret Term Project


import utime
import cotask
import task_share
import gc
import mlx_cam_mod
import servo
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


def take_picture(camera):
    """!
    @brief	Take a picture from the camera and find the centroid of the largest heat signature.
    @param	Camera Object created by MLX_Cam()
    @return	Array of x and y points for the turret to point.
    """
    image = get_image()
    
    
def move_motors(x, y):
    """!
    @brief	Take a picture from the camera and find the centroid of the largest heat signature.
    @param	x The point to move the yaw axis motor to move to.
    @ param	y The point to move the pitch axis motor to move to.
    @return	
    """
    pass
    
def shoot():
    """!
    @brief	Fires the turret by moving the servo to set positions.
    @return	
    """
    ser.set_pos(20)
    utime.sleepms(50)
    ser.set_pos(0)


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
                move_motors();
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
    """!@brief	This script creates instances of all the required modules and
            calls the test program in main()
        @details	The classes have to be instantiated here outside of functions
            so that their values can be accessed and changed by any function.
    """
    gc.collect()
    
    # Initialize encoder objects
    enc_yaw = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    enc_pitch = EncoderDriver(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    # Initialize motor objects
    motor_yaw = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    motor_pitch = MotorDriver (pyb.Pin.board.PC1,pyb.Pin.board.PA0,pyb.Pin.board.PA1,5)
    # Initialize proportional controllers with default values
    con_yaw = ProControl()
    con_pitch = ProControl()
    
    
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
    
    
    
    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(task1_yaw_motor, name="Task_1", priority=1, period=20,
                        profile=False, trace=False)
    task2 = cotask.Task(task2_pitch_motor, name="Task_2", priority=1, period=20,
                        profile=False, trace=False)
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)
    
    # Create  servo object for firing
    ser = Servo(pyb.Pin.board.PB10,2,3)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()
    
    main()