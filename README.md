# ME405_TermProject
Created by Tristan de Lemos, Trenten Spicer, Rees Verleur

We have created a turret that fires a projectile after taking a picture and taking aim at the warmest spot from the picture. The purpose of this device is to be able to aim and fire a turret autonomously. It's intended use is for security or defense contracting, so that whenever a foreign object is detected the turret will fire.

## Hardware Design Overview

INSERT PHOTO OF TURRET


## Software Design Overview

The software is designed as a finite state machine. The main functionality of the project is in main.py with all other files supporting it.
The full overview of the software design 
https://tristandelemos.github.io/ME405_TermProject/


## Discussion of Results

A discussion of the results.  How did you test your system?  How well has your system performed in these tests


A brief discussion of what you've learned about the project and recommendations for anyone who would like to build upon your work:
I would have the coders look deeper into tasks and see if that would make the system faster than it is now.

Shown below is the FSM for our system.

![alt text](State_Diagram.png)

For the motor task and the take picture task, we have state machines as well.

![alt text](motor_task.png)
![alt text](picture_task.png)
