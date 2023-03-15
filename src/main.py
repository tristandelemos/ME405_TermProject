# Created by Tristan de Lemos, Trenten Spicer, and Rees Verleur
#
# main file for Turret Term Project


import utime
import cotask
import task_share
import gc
import mlx_cam_mod as camera
import servo
import pyb
from machine import Pin, I2C
from encoder_driver import EncoderDriver
from motor_driver import MotorDriver
from pid_control import PidControl
#from pro_control import ProControl


S0_INIT = 0
S1_TAKE_PICTURE = 1
S2_MOVE_MOTORS = 2
S3_SHOOT = 3
S4_PAUSE = 4

def task_motors():
    """!@brief Task which runs the proportional controller to control the yaw motor.

    """
    # Read encoder to get an initial value
    read_yaw = enc_yaw.read()
    read_pitch = enc_pitch.read()
    # Zero the position so that the step response moves a known amount
    pos_yaw = 0
    pos_pitch = 0
    # Record the start time for later use
    start_yaw = utime.ticks_ms()
    start_pitch = utime.ticks_ms()
    
    while True:
        # Update the read and postion values
        read_yaw,pos_yaw = enc_yaw.update(read_yaw,pos_yaw)
        read_pitch,pos_pitch = enc_pitch.update(read_pitch,pos_pitch)
    
        # Calculate effort with pos and neg limits
        effort_yaw = con_yaw.run(pos_yaw)
        effort_pitch = con_pitch.run(pos_pitch)
        
        if effort_yaw<-100:
            effort_yaw = -100
        elif effort_yaw>100:
            effort_yaw = 100
            
        if effort_pitch<-100:
            effort_pitch = -100
        elif effort_pitch>100:
            effort_pitch = 100
            
        # Set the motor duty cycle
        motor_yaw.set_duty_cycle(effort_yaw)
        motor_pitch.set_duty_cycle(effort_pitch)
        # Yield and come back at top of while loop in next call
        yield

def turn_around():
    """!
    @brief	Turn the yaw axis motor to turn 180 degrees
    """
    # need to find the point to turn 180 degrees
    con_yaw.set_setpoint(-3000)
    con_pitch.set_setpoint(500)

    # Read encoder to get an initial value
    read_yaw = enc_yaw.read()
    read_pitch = enc_pitch.read()
    # Zero the position so that the step response moves a known amount
    pos_yaw = 0
    pos_pitch = 0
    
    while True:
        # Update the read and postion values
        read_yaw,pos_yaw = enc_yaw.update(read_yaw,pos_yaw)
        read_pitch,pos_pitch = enc_pitch.update(read_pitch,pos_pitch)
    
        # Calculate effort with pos and neg limits
        effort_yaw = con_yaw.run(pos_yaw)
        effort_pitch = con_pitch.run(pos_pitch)
        
        if effort_yaw<-100:
            effort_yaw = -100
        elif effort_yaw>100:
            effort_yaw = 100
            
        if effort_pitch<-100:
            effort_pitch = -100
        elif effort_pitch>100:
            effort_pitch = 100
            
        # Set the motor duty cycle
        motor_yaw.set_duty_cycle(effort_yaw)
        motor_pitch.set_duty_cycle(effort_pitch)
        # Yield and come back at top of while loop in next call
        yield effort_yaw, effort_yaw


def take_picture(camera):
    """!
    @brief	Take a picture from the camera and find the centroid of the largest heat signature.
    @param	Camera Object created by MLX_Cam()
    @return	Array of x and y points for the turret to point.
    """
    image = get_image()
    
    
    return x, y
    # find centroid
    
    
def move_motors(x, y):
    """!
    @brief	set new set points for both motors
    @param	x The point to move the yaw axis motor to move to.
    @ param	y The point to move the pitch axis motor to move to.
    @return	
    """
    con_yaw.set_setpoint(x)
    con_pitch.set_setpoint(y)
    
    
    read_yaw,pos_yaw = enc_yaw.update(read_yaw,pos_yaw)
    read_pitch,pos_pitch = enc_pitch.update(read_pitch,pos_pitch)
    
    effort_yaw = con_yaw.run(pos_yaw)
    effort_pitch = con_picth.run(pos_pitch)
    
    effort_yaw = min(max(-100,effort_yaw),100)
    effort_pitch = min(max(-100,effort_pitch),100)
        
    motor_yaw.set_duty_cycle(effort_yaw)
    motor_pitch.set_duty_cycle(effort_pitch)
    
    
def shoot():
    """!
    @brief	Fires the turret by moving the servo to set positions.
    @return	
    """
    ser.set_pos(20)
    utime.sleepms(50)
    ser.set_pos(0)


def main():
    
    yaw_position  = 0
    pitch_position = 0
    
    state = S0_INIT
    
    while(True):
        
        try:
            cotask.task_list.pri_sched()
            
            if(state == S0_INIT):
                # move yaw motor to turn around
                state = S1_TAKE_PICTURE
            
            
            # Take picture and find warmest area to shoot at
            if(state == S1_TAKE_PICTURE):
                # this is how we are going to wait those five seconds
                #if(input() == 'y'):
                image_array = camera.get_bytes(image)
                yaw_position, pitch_position = calculate_centroid_bytes(ref_array, image_array)
                
        
                state = S2_MOVE_MOTORS
        
            # Move motors to desired angles
            if(state == S2_MOVE_MOTORS):
                cotask.task_list.append(task2)
                
                state = S3_SHOOT
            
            # activate servo to shoot
            if(state == S3_SHOOT):
                shoot()
    
                state = S4_PAUSE
       
            # pause to allow for reloading
            if(state == S4_PAUSE):
                
                utime.sleep(5)
                
                state = S1_TAKE_PICTURE
       
        except KeyboardInterrupt:
            # If there is a keyboard interrupt, turn off the motors
            motor_1.set_duty_cycle(0)
            motor_2.set_duty_cycle(0)
            # Tell the C-Python program that we are done
            u2.write(b'end\r\n')
            # Print exit statement
            print('Program exited by user')
            # Raise exception to exit out of all loops
            raise Exception('Program Exited by User')
            break 
    
if __name__ == "__main__":
    """!@brief	This script creates instances of all the required modules and
            calls the test program in main()
        @details	The classes have to be instantiated here outside of functions
            so that their values can be accessed and changed by any function.
    """
    gc.collect()
    
    # Initialize encoder objects
    enc_yaw = EncoderDriver(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    enc_pitch = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    # Initialize motor objects
    motor_yaw = MotorDriver (pyb.Pin.board.PC1,pyb.Pin.board.PA0,pyb.Pin.board.PA1,5)
    motor_pitch = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    # Initialize proportional controllers with default values
    con_yaw = PidControl(Kp = 0.15,Ki = 0.0001,Kd = 0.03)
    con_pitch = PidControl(Kp = 0.15,Ki = 0.0001,Kd = 0.03)
    
    
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
    camera = mlx_cam_mod.MLX_Cam(i2c_bus)
    
    pitch = 500
    yaw  = -3000
    
    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    
    
    task1 = cotask.Task(turn_around, name="Task_1", priority=1, period=20,
                        profile=False, trace=False)
    task2 = cotask.Task(task_motors, name="Task_1", priority=1, period=20,
                        profile=False, trace=False)
    
    #task2 = cotask.Task(task2_pitch_motor, name="Task_2", priority=1, period=20,
     #                   profile=False, trace=False)
    cotask.task_list.append(task1)
    #cotask.task_list.append(task2)
    
    # Create  servo object for firing
    ser = Servo(pyb.Pin.board.PB10,2,3)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()
    
    main()