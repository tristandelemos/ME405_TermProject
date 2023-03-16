# Created by Tristan de Lemos, Trenten Spicer, and Rees Verleur
#
# main file for Turret Term Project


import utime
import cotask
import task_share
import gc
import mlx_cam_mod as camera
#import mlx_cam as camera
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
    utime.sleep_ms(50)
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
                #image = cam.get_image()
                #image_array = cam.get_bytes(image)
                #yaw_position, pitch_position = cam.calculate_centroid_bytes(ref_array, image_array)
                
        
                state = S2_MOVE_MOTORS
        
            # Move motors to desired angles
            if(state == S2_MOVE_MOTORS):
                #cotask.task_list.append(task2)
                
                state = S3_SHOOT
            
            # activate servo to shoot
            if(state == S3_SHOOT):
                #shoot()
    
                state = S4_PAUSE
       
            # pause to allow for reloading
            if(state == S4_PAUSE):
                
                
                
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
        
        except:
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
    
    # Intitialize camera
    
    #from pyb import info

    i2c_bus = I2C(1)
    
    #print('Allocated = ',gc.mem_alloc())
    #print('Free = ',gc.mem_free())
    # Create the camera object and set it up in default mode
    gc.collect()
    cam = camera.MLX_Cam(i2c_bus)
    ref_array = bytearray(b'\xea\xe6\xea\xe6\xe8\xe5\xe8\xe5\xe8\xe3\xe8\xe4\xe8\xe2\xe7\xe3\xe9\xe1\xe7\xe3\xe9\xe2\xe8\xe2\xe9\xe1\xe9\xe2\xe7\xe1\xea\xdf\xe7\xe5\xe3\xe2\xe6\xe5\xe2\xe2\xe5\xe3\xe2\xe1\xe5\xe2\xe1\xe0\xe5\xe1\xe1\xdf\xe6\xe1\xe3\xdf\xe6\xe1\xe3\xde\xe5\xe0\xe4\xdd\xe9\xe5\xe8\xe6\xe7\xe3\xe8\xe4\xe8\xe3\xe7\xe3\xe6\xe2\xe6\xe2\xe8\xe2\xe7\xe3\xe8\xe2\xe6\xe2\xe8\xe1\xe8\xe2\xe8\xe1\xe8\xdf\xe5\xe5\xe3\xe3\xe4\xe3\xe2\xe1\xe5\xe2\xe2\xe0\xe4\xe1\xe1\xdf\xe5\xe0\xe2\xdf\xe5\xe1\xe1\xdf\xe5\xe0\xe3\xdf\xe5\xe0\xe3\xdc\xe9\xe5\xe8\xe6\xe9\xe4\xe8\xe4\xe8\xe2\xe7\xe3\xe8\xe2\xe6\xe2\xe9\xe2\xe7\xe2\xe8\xe1\xe7\xe2\xe9\xe0\xe7\xe1\xe8\xe0\xe7\xde\xe6\xe4\xe1\xe1\xe6\xe2\xe1\xe0\xe5\xe1\xe1\xdf\xe5\xe1\xe1\xdf\xe6\xe1\xe1\xdf\xe5\xe1\xe2\xdf\xe6\xdf\xe3\xdf\xe5\xdf\xe3\xdc\xe9\xe5\xe7\xe5\xe7\xe4\xe7\xe4\xe7\xe3\xe7\xe3\xe6\xe1\xe7\xe2\xe8\xe2\xe7\xe2\xe7\xe1\xe6\xe2\xe8\xe1\xe8\xe1\xe8\xe0\xe8\xdf\xe5\xe3\xe1\xe1\xe4\xe3\xe0\xe0\xe3\xe1\xe1\xdf\xe3\xe0\xe0\xde\xe4\xe1\xe1\xde\xe4\xe0\xe1\xde\xe6\xdf\xe1\xde\xe5\xdf\xe3\xdb\xe8\xe6\xe7\xe5\xe7\xe3\xe7\xe4\xe7\xe2\xe6\xe3\xe5\xe2\xe6\xe2\xe7\xe1\xe6\xe2\xe6\xe1\xe7\xe2\xe8\xe0\xe7\xe1\xe8\xe0\xe8\xdf\xe4\xe2\xe0\xe1\xe2\xe1\xe1\xdf\xe3\xe0\xdf\xde\xe1\xe0\xdf\xde\xe4\xdf\xe0\xde\xe4\xdf\xe1\xde\xe5\xdf\xe0\xdd\xe5\xdf\xe2\xdc\xe9\xe5\xe7\xe5\xe8\xe4\xe7\xe4\xe7\xe2\xe5\xe2\xe6\xe1\xe6\xe2\xe7\xe1\xe7\xe2\xe8\xe1\xe7\xe2\xe8\xe0\xe6\xe1\xe6\xe0\xe7\xde\xe4\xe1\xdf\xe0\xe3\xe2\xe0\xdf\xe3\xe1\xdf\xde\xe2\xdf\xdf\xde\xe3\xde\xe0\xde\xe4\xdf\xe0\xdd\xe4\xde\xe0\xdd\xe3\xde\xe1\xdb\xe7\xe4\xe6\xe4\xe5\xe3\xe5\xe4\xe5\xe2\xe5\xe1\xe5\xe1\xe5\xe1\xe6\xe1\xe5\xe1\xe7\xe1\xe6\xe2\xe7\xe1\xe6\xe1\xe6\xdf\xe7\xdf\xe3\xe1\xde\xdf\xe1\xdf\xde\xde\xe1\xde\xde\xdc\xe0\xdf\xde\xdc\xe1\xde\xde\xdc\xe3\xde\xe0\xde\xe3\xde\xdf\xdc\xe3\xde\xe1\xda\xe5\xe5\xe5\xe5\xe6\xe3\xe6\xe3\xe5\xe1\xe4\xe1\xe5\xe1\xe5\xe1\xe6\xe1\xe5\xe1\xe6\xe1\xe6\xe1\xe7\xe0\xe6\xe1\xe5\xdf\xe7\xde\xe0\xe1\xdd\xde\xe1\xdf\xdd\xde\xe0\xde\xdc\xdc\xe0\xdd\xdd\xdc\xe1\xde\xdd\xdc\xe2\xde\xde\xdc\xe3\xde\xdf\xdc\xe2\xde\xe0\xda\xe5\xe4\xe5\xe4\xe5\xe2\xe4\xe1\xe5\xe0\xe3\xe1\xe5\xe0\xe3\xe0\xe6\xe0\xe5\xe1\xe5\xdf\xe5\xe1\xe6\xdf\xe5\xdf\xe5\xdf\xe5\xdd\xe0\xdf\xdc\xdd\xdf\xde\xdc\xdc\xdf\xde\xdc\xdb\xdf\xdd\xdc\xdb\xe1\xdd\xdd\xdb\xe1\xde\xdd\xdc\xe3\xdd\xde\xdb\xe1\xdd\xdf\xd9\xe3\xe3\xe4\xe3\xe3\xe1\xe4\xe1\xe3\xe0\xe4\xe1\xe3\xe0\xe4\xe0\xe3\xdf\xe5\xe1\xe4\xdf\xe5\xdf\xe5\xdf\xe4\xdf\xe5\xdf\xe6\xde\xdd\xde\xda\xdc\xde\xdd\xdb\xdc\xdd\xdc\xdb\xda\xde\xdc\xda\xdb\xdf\xdc\xdc\xda\xdf\xdc\xdc\xda\xe1\xdc\xdd\xda\xe1\xdc\xde\xd9\xe3\xe2\xe3\xe3\xe2\xe1\xe3\xe1\xe3\xe0\xe3\xe1\xe2\xe0\xe3\xe1\xe3\xdf\xe5\xe0\xe4\xdf\xe4\xe0\xe5\xdf\xe4\xdf\xe3\xde\xe5\xde\xdb\xdd\xd9\xdb\xdc\xdc\xda\xda\xdd\xdc\xda\xda\xdc\xdc\xda\xd9\xde\xdc\xdb\xd9\xde\xdc\xdb\xda\xe0\xda\xdc\xd9\xdf\xdc\xdc\xd8\xe2\xe2\xe2\xe3\xe2\xe1\xe3\xe1\xe2\xdf\xe1\xdf\xe1\xdf\xe2\xdf\xe4\xdf\xe3\xe0\xe4\xdf\xe3\xdf\xe3\xde\xe2\xdf\xe2\xde\xe2\xdd\xd7\xd9\xd4\xd7\xd8\xd9\xd5\xd6\xd8\xd8\xd5\xd6\xd8\xd7\xd6\xd5\xda\xd7\xd5\xd6\xda\xd7\xd6\xd5\xda\xd7\xd7\xd6\xda\xd8\xd9\xd4')
    # Initialize encoder objects
    enc_yaw = EncoderDriver(Pin.board.PC6, Pin.board.PC7, 8)
    enc_pitch = EncoderDriver( Pin.board.PB6,  Pin.board.PB7, 4)
    # Initialize motor objects
    motor_yaw = MotorDriver ( Pin.board.PC1, Pin.board.PA0, Pin.board.PA1,5)
    motor_pitch = MotorDriver ( Pin.board.PA10, Pin.board.PB4, Pin.board.PB5,3)
    # Initialize proportional controllers with default values
    con_yaw = PidControl(Kp = 0.15,Ki = 0.0001,Kd = 0.03)
    con_pitch = PidControl(Kp = 0.15,Ki = 0.0001,Kd = 0.03)
    
    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    
    
    task1 = cotask.Task(turn_around, name="Task_1", priority=1, period=20,
                        profile=False, trace=False)
    task2 = cotask.Task(task_motors, name="Task_1", priority=2, period=20,
                        profile=False, trace=False)
    
    #task2 = cotask.Task(task2_pitch_motor, name="Task_2", priority=1, period=20,
     #                   profile=False, trace=False)
    cotask.task_list.append(task1)
    #cotask.task_list.append(task2)
    
    # Create  servo object for firing
    ser = servo.Servo( Pin.board.PB10,2,3)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()
    
    main()