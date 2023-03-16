"""!
@file main.py

This file contains the state machine which operates the turret. The file requires
several standard libraries as well as 5 custom made modules which control the encoders,
the motors, the servo, and the camera. As well as a PID controller

@author T DeLemos Created finite state machine
@author R Verleur Created servo driver, PID loop, and added byte operations to camera module
@author T Spicer Added functions to extract centroid/angle data from byte array
"""

import utime
import gc
import mlx_cam_mod as camera
import servo
import pyb
from machine import Pin, I2C
from encoder_driver import EncoderDriver
from motor_driver import MotorDriver
from pid_control import PidControl




S0_INIT = 0
S1_TAKE_PICTURE = 1
S2_MOVE_MOTORS = 2
S3_SHOOT = 3
S4_PAUSE = 4

state = S0_INIT

def task_motors(pitch, yaw):
    """!@brief Task which runs the PID controller to control the positioning motors.
        @details This task runs the PID loop to position the motors after the initial
        turn around
        @param pitch The pitch angle to move the motor to
        @param yaw The yaw angle to move the motor to
        @returns an integer representing if the target has been reached within a specified tolerance
    """
    # Set gains for PID loop
    con_yaw.set_Kp(0.57)
    con_yaw.set_Ki(0)
    con_yaw.set_Kd(0)
    
    con_pitch.set_Kp(0.5)
    con_pitch.set_Ki(0.0007)
    con_pitch.set_Kd(0)
    
    # Read initial positions for reference
    read_yaw = enc_yaw.read()
    read_pitch = enc_pitch.read()
    # Zero the position so that the step response moves relative to current position
    pos_yaw = 0
    pos_pitch = 0
    
    # Set setpoints for position
    con_yaw.set_setpoint(yaw)
    con_pitch.set_setpoint(pitch)
    
    while True:
        # Update the read and postion values
        read_yaw,pos_yaw = enc_yaw.update(read_yaw,pos_yaw)
        read_pitch,pos_pitch = enc_pitch.update(read_pitch,pos_pitch)
    
        # Calculate effort with pos and neg limits
        effort_yaw = con_yaw.run(pos_yaw)
        effort_pitch = con_pitch.run(pos_pitch)
        
        # Print error for debugging
        print(con_yaw.err)
        print(con_pitch.err)

        # If you get within 15 ticks of postion
        if(abs(con_yaw.err) <= 15 and abs(con_pitch.err) <= 10):
            motor_yaw.set_duty_cycle(0)
            motor_pitch.set_duty_cycle(0)
            # Return 0 (transitions to next state)
            yield 0
            
        # Limit efforts
        if effort_yaw<-100:
            effort_yaw = -100
        elif effort_yaw>100:
            effort_yaw = 100
            
        if effort_pitch<-80:
            effort_pitch = -80
        elif effort_pitch>80:
            effort_pitch = 80
            
        # Set the motor duty cycle
        motor_yaw.set_duty_cycle(effort_yaw)
        motor_pitch.set_duty_cycle(effort_pitch)
        # Yield and come back at top of while loop in next call
        yield 1

def turn_around():
    """!
    @brief	Turn the yaw axis motor to turn 180 degrees
    @details This task runs the PID loop to turn the turret 180 degrees and
             center it vertically
    @returns	An integer representing that the target has been reached
    """
    # Point to turn 180 and center pitch axis
    con_yaw.set_setpoint(-3008)
    con_pitch.set_setpoint(500)

    # Read encoder to get an initial value
    read_yaw = enc_yaw.read()
    read_pitch = enc_pitch.read()
    # Zero the position so that the step response moves relative to current position
    pos_yaw = 0
    pos_pitch = 0
    
    while True:
        # Update the read and postion values
        read_yaw,pos_yaw = enc_yaw.update(read_yaw,pos_yaw)
        read_pitch,pos_pitch = enc_pitch.update(read_pitch,pos_pitch)
    
        # Calculate effort with pos and neg limits
        effort_yaw = con_yaw.run(pos_yaw)
        effort_pitch = con_pitch.run(pos_pitch)
        print(con_yaw.err)
        
        # if close enough, go to next state and stop doing this function
        if(abs(con_yaw.err) <= 5 and abs(con_pitch.err)):
            motor_yaw.set_duty_cycle(0)
            motor_pitch.set_duty_cycle(0)
            #print("popped off")
            #state = S1_TAKE_PICTURE
            #cotask.task_list.pop()
            yield 0
            
        # Limit efforts
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
        yield 1
    
def shoot():
    """!
    @brief	Fires the turret by moving the servo to set positions.
    @details Fires the turret by moving the servo to a fire position, delaying
             then returning to a non firing position. Makes use of the custom
             servo module
    """
    ser.set_pos(-10)
    utime.sleep_ms(100)
    ser.set_pos(20)

def main():
    """!
    @brief The finite state machine for the turret operation
    @details This function steps through each state in turn and implements the
    appropriate transition logic. The program does not use cotask because the program
    was not able to allocate memory appropriately when cotask was included.
    """
    
    yaw_position  = 0
    pitch_position = 0
    
    state = S0_INIT
        
    while(True):
        
        try:
            if(state == S0_INIT):
                # move yaw motor to turn around
                x = turn_around()
                while(next(x) != 0):
                    utime.sleep_ms(20)
                
                state = S1_TAKE_PICTURE
            
            # Take picture and find centroid of hot pixels to fire at
            if(state == S1_TAKE_PICTURE):
                # this is how we are going to wait those five seconds
                while(utime.ticks_diff(utime.ticks_ms(), start_time) <= 5500):
                    pass
                
                image = cam.get_image()
                image_array = cam.get_bytes(image)
                yaw_angle, pitch_angle = cam.find_angle(ref_array, image_array,limit = 100)

                print("yaw angle:", yaw_angle)
                print("pitch angle:", pitch_angle)
                
                if yaw_angle != -60:
                    yaw_position = round(yaw_angle * (6016/360))-yaw_offset
                    pitch_position = round(pitch_angle * (3609.6/360))-pitch_offset
                    print(yaw_position)
                    print(pitch_position)
        
                    state = S2_MOVE_MOTORS
                else:
                    state = S1_TAKE_PICTURE
                
        
            # Move motors to desired angles
            if(state == S2_MOVE_MOTORS):
                print("in state 2")
                x = task_motors(pitch_position, yaw_position)
                while(next(x) != 0):
                    utime.sleep_ms(20)
                    
                
                state = S3_SHOOT
            
            # activate servo to shoot
            if(state == S3_SHOOT):
                print("fire!")
                shoot()
                utime.sleep_ms(5000)
            # move back to center to allow for reloading and another shot
                x = task_motors(-pitch_position, -yaw_position)
                while(next(x) != 0):
                    utime.sleep_ms(20)
    
                state = S4_PAUSE
       
            # pause to allow for reloading
            if(state == S4_PAUSE):
                
                utime.sleep(10)
                
                state = S1_TAKE_PICTURE
       
        except KeyboardInterrupt:
            # If there is a keyboard interrupt, turn off the motors
            motor_yaw.set_duty_cycle(0)
            motor_pitch.set_duty_cycle(0)
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
                
    start_time = utime.ticks_ms()
    yaw_offset = -40
    pitch_offset = -50
    # Intitialize camera

    i2c_bus = I2C(1)
    
    # Create the camera object and set it up in default mode
    gc.collect()
    cam = camera.MLX_Cam(i2c_bus)
    # Explicitly define reference array with bytes (768 bytes)
    ref_array = bytearray(b'\xe9\xe6\xea\xe7\xe9\xe5\xe8\xe6\xe8\xe5\xe9\xe5\xe7\xe2\xe6\xe3\xe8\xe1\xe7\xe3\xe8\xe1\xe6\xe2\xe8\xe1\xe7\xe1\xe6\xe0\xe8\xdf\xe7\xe5\xe3\xe3\xe5\xe3\xe3\xe1\xe6\xe4\xe3\xe1\xe5\xe1\xe1\xdf\xe5\xe1\xe1\xdf\xe5\xe0\xe1\xdf\xe5\xe0\xe3\xde\xe4\xdf\xe3\xdc\xe8\xe5\xe8\xe6\xe7\xe4\xe8\xe5\xe8\xe3\xe8\xe4\xe6\xe2\xe7\xe3\xe8\xe1\xe7\xe2\xe7\xe1\xe6\xe1\xe6\xdf\xe6\xe1\xe8\xdf\xe8\xdf\xe6\xe5\xe3\xe3\xe4\xe3\xe2\xe1\xe5\xe3\xe1\xe0\xe4\xe1\xe1\xdf\xe5\xe0\xe1\xdf\xe5\xdf\xe1\xde\xe5\xdf\xe1\xde\xe4\xe0\xe2\xdc\xe9\xe5\xe9\xe6\xea\xe5\xe8\xe6\xe9\xe3\xe8\xe4\xe9\xe3\xe7\xe3\xe9\xe2\xe7\xe3\xe8\xe0\xe7\xe1\xe8\xdf\xe6\xe0\xe6\xe0\xe7\xdf\xe5\xe4\xe2\xe1\xe6\xe3\xe2\xe1\xe6\xe2\xe2\xe1\xe5\xe2\xe1\xdf\xe6\xe2\xe2\xdf\xe5\xdf\xe1\xdd\xe5\xdf\xe1\xdd\xe4\xde\xe1\xdb\xe8\xe4\xe6\xe5\xe8\xe4\xe7\xe5\xe6\xe3\xe7\xe4\xe6\xe2\xe7\xe3\xe6\xe2\xe7\xe1\xe6\xdf\xe5\xe0\xe8\xdf\xe6\xe1\xe6\xdf\xe8\xde\xe4\xe1\xdd\xde\xe3\xe2\xdf\xdf\xe3\xe1\xe0\xdf\xe2\xe1\xdf\xde\xe4\xe0\xe0\xdd\xe3\xdc\xdd\xda\xe3\xde\xe1\xdc\xe4\xde\xe2\xda\xe8\xe5\xe7\xe5\xe6\xe4\xe7\xe5\xe7\xe3\xe8\xe6\xed\xea\xe9\xe5\xe8\xe2\xe7\xe3\xe6\xdf\xe6\xe1\xe6\xdf\xe6\xe0\xe6\xdf\xe7\xdf\xe3\xe3\xdf\xe1\xe3\xe1\xe0\xdf\xe3\xe1\xdf\xdf\xe5\xe4\xe0\xdf\xe5\xdf\xe0\xde\xe3\xde\xdf\xdc\xe4\xde\xdf\xdb\xe5\xde\xe1\xda\xe8\xe5\xe6\xe5\xe6\xe3\xe6\xe3\xe6\xe2\xe5\xe2\xe5\xe1\xe5\xe1\xe5\xdf\xe6\xe1\xe6\xdf\xe5\xdf\xe6\xdf\xe5\xe0\xe5\xde\xe7\xde\xe3\xe1\xde\xde\xe2\xe0\xde\xde\xe2\xdf\xde\xdd\xe1\xde\xde\xdc\xe2\xdd\xde\xdc\xe3\xde\xde\xdb\xe3\xdd\xde\xdc\xe2\xdd\xe1\xd9\xe6\xe3\xe5\xe3\xe4\xe2\xe5\xe3\xe5\xe1\xe6\xe1\xe4\xe0\xe4\xe1\xe5\xdf\xe3\xe0\xe5\xde\xe5\xe0\xe5\xde\xe5\xdf\xe5\xde\xe6\xde\xe1\xdf\xdc\xdc\xdf\xde\xdc\xdd\xe1\xdf\xdd\xdc\xdf\xde\xdd\xda\xe1\xdd\xdd\xdb\xe1\xdc\xdd\xdb\xe2\xdc\xde\xdb\xe1\xdc\xdf\xda\xe4\xe3\xe5\xe4\xe5\xe1\xe5\xe3\xe5\xe0\xe5\xe2\xe5\xdf\xe4\xe1\xe5\xe0\xe3\xdf\xe4\xdf\xe4\xdf\xe5\xde\xe4\xdf\xe3\xde\xe5\xde\xdf\xdf\xdc\xdc\xe0\xdd\xdb\xdc\xdf\xdd\xdb\xdb\xdf\xdc\xdc\xda\xe0\xdc\xdc\xda\xdf\xdc\xdc\xda\xe0\xdc\xdd\xd9\xe0\xdc\xde\xd8\xe5\xe4\xe4\xe3\xe4\xe1\xe4\xe2\xe4\xe0\xe3\xe1\xe5\xe0\xe3\xe0\xe5\xdf\xe3\xdf\xe3\xde\xe3\xdf\xe4\xdc\xe3\xde\xe3\xdd\xe3\xdc\xdf\xdf\xdb\xdc\xde\xde\xdb\xdb\xdf\xdc\xdb\xda\xdf\xdc\xdb\xd9\xe0\xdc\xdb\xd9\xde\xdb\xdb\xd9\xe0\xda\xdd\xd8\xdf\xdb\xde\xd7\xe2\xe2\xe3\xe3\xe3\xe1\xe3\xe1\xe3\xe1\xe4\xe1\xe3\xdf\xe4\xe1\xe3\xde\xe3\xde\xe3\xdd\xe3\xdf\xe4\xdd\xe3\xdf\xe4\xde\xe5\xde\xdc\xdd\xd9\xdb\xdd\xdc\xda\xd9\xdd\xdc\xdb\xda\xde\xdc\xdb\xdb\xdf\xdb\xda\xd9\xde\xda\xdb\xd9\xe0\xda\xdb\xd9\xde\xda\xdd\xd8\xe2\xe3\xe2\xe2\xe3\xe1\xe3\xe1\xe3\xe0\xe3\xe1\xe3\xe0\xe4\xe1\xe3\xde\xe3\xdf\xe4\xde\xe3\xdf\xe4\xde\xe3\xde\xe3\xdd\xe5\xdf\xdb\xdc\xd8\xda\xdb\xdb\xd9\xd9\xdc\xdb\xd9\xd9\xdc\xdc\xda\xd9\xdd\xda\xd9\xd7\xdd\xda\xda\xd8\xde\xda\xda\xd9\xde\xdb\xdc\xd8\xe2\xe2\xe2\xe3\xe2\xe1\xe3\xe1\xe2\xe0\xe1\xe0\xe2\xdf\xe3\xe0\xe3\xde\xe2\xdf\xe3\xde\xe2\xdf\xe3\xde\xe2\xdf\xe1\xde\xe2\xdd\xd7\xd8\xd3\xd6\xd7\xd8\xd4\xd5\xd8\xd8\xd5\xd5\xd8\xd7\xd6\xd4\xd9\xd6\xd4\xd5\xd9\xd6\xd5\xd4\xda\xd6\xd5\xd4\xd9\xd7\xd8\xd3')
    # Initialize encoder objects
    enc_yaw = EncoderDriver(Pin.board.PC6, Pin.board.PC7, 8)
    enc_pitch = EncoderDriver( Pin.board.PB6,  Pin.board.PB7, 4)
    # Initialize motor objects
    motor_yaw = MotorDriver ( Pin.board.PC1, Pin.board.PA0, Pin.board.PA1,5)
    motor_pitch = MotorDriver ( Pin.board.PA10, Pin.board.PB4, Pin.board.PB5,3)
    # Initialize proportional controllers with default values
    con_yaw = PidControl(Kp = 0.15,Ki = 0.0002,Kd = 0.03)
    con_pitch = PidControl(Kp = 0.15,Ki = 0.0002,Kd = 0.03)
    
    
    # Create  servo object for firing
    ser = servo.Servo( Pin.board.PB10,2,3)
    ser.set_pos(20)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time operation is started
    gc.collect()
    
    main()