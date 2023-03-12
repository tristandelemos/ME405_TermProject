"""!
@file basic_tasks.py
    This file contains a demonstration program that runs some tasks, an
    inter-task shared variable, and a queue. The tasks don't really @b do
    anything; the example just shows how these elements are created and run.

@author JR Ridgely
@date   2021-Dec-15 JRR Created from the remains of previous example
@copyright (c) 2015-2021 by JR Ridgely and released under the GNU
    Public License, Version 2. 
"""

import gc
import pyb
import cotask
import task_share
from Servo import servo
from encoder_driver import EncoderDriver
from motor_driver import MotorDriver
from pid_control import PidControl
import utime


def initialize():
    encA = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    motorA = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    encB = EncoderDriver(pyb.Pin.board.PC7, pyb.Pin.board.PC7,8)
    motorB = MotorDriver(pyb.Pin.board.PC1,pyb.Pin.board.A0,pyb.Pin.board.A1,5)
    conA = PidControl(kp = 1,ki = 0,kd = 0)
    conB = PidControl(kp = 1,ki = 0,kd = 0)
    readA = encA.read()
    readB = encB.read()
    posA = 0
    posB = 0


def set_pos(az,el):
    """!
    Task which puts things into a share and a queue.
    @param shares A list holding the share and queue used by this task
    """
    conA.set_setpoint(az)
    conB.set_setpoint(el)
    
    
    readA,posA = encA.update(readA,posA)
    readB,posB = encB.update(readB,posB)
    
    effortA = conA.run(posA)
    effortA = conB.run(posB)
    
    effortA = min(max(-100,effortA),100)
    effortB = min(max(-100,effortB),100)
        
    motorA.set_duty_cycle(effortA)
    motorB.set_duty_cycle(effortB)
    
    return conA.err,conB.err


def fire(errA,errB,threshold):
    """!
    Task which takes things out of a queue and share and displays them.
    @param shares A tuple of a share and queue from which this task gets data
    """
    if errA <= threshold and errB <= threshold:
        Servo.set_pos(0)
        utime.sleepms(50)
        Servo.set_pos(20)

# This code creates a share, a queue, and two tasks, then starts the tasks. The
# tasks run until somebody presses ENTER, at which time the scheduler stops and
# printouts show diagnostic information about the tasks, share, and queue.
if __name__ == "__main__":
    print("Testing ME405 stuff in cotask.py and task_share.py\r\n"
          "Press Ctrl-C to stop and show diagnostics.")

    # Create a share and a queue to test function and diagnostic printouts
    share0 = task_share.Share('h', thread_protect=False, name="Share 0")
    q0 = task_share.Queue('L', 16, thread_protect=False, overwrite=False,
                          name="Queue 0")

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(task1_fun, name="Task_1", priority=1, period=400,
                        profile=True, trace=False, shares=(share0, q0))
    task2 = cotask.Task(task2_fun, name="Task_2", priority=2, period=1500,
                        profile=True, trace=False, shares=(share0, q0))
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()

    # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
    while True:
        try:
            cotask.task_list.pri_sched()
        except KeyboardInterrupt:
            break

    # Print a table of task data and a table of shared information data
    print('\n' + str (cotask.task_list))
    print(task_share.show_all())
    print(task1.get_trace())
    print('')

