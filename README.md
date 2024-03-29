# ME405_TermProject
Created by Tristan de Lemos, Trenten Spicer, Rees Verleur

We have created a turret that fires a projectile after taking a picture and taking aim at the warmest spot from the picture. The purpose of this device is to be able to aim and fire a turret autonomously. It's intended use is for security or defense contracting, so that whenever a foreign object is detected the turret will fire.

## Hardware Design Overview
The hardware was designed around a purchased nerf gun. The gun was disassembled to strip down the weight and size, and a custom clamshell was printed to contain the mechanical components. A clevis was designed to allow for rotation in two axes, and gt2 belts were selected for their low backlash and availability. Tensioners were used to be sure the belts would not slip. The motors were sized to draw the maximum allowable current at stall to be sure that the motor driver was not burned out. A servo was selected for the firing mechanism because of the ease of use and their reliability. The camera was mounted on a toothed device which allows for adjustment in  $5^\{o}$ increments. The device was wired using a breadboard since it needs to be easy to disassemble. 3D printing was selected for manufacturing due to the complicated geometries of the required parts, as well as the low requirements for strength and the low cost.
<div align="center">
  <img src="src/hardware1.jpg" alt="Alt text">
  <img src="src/hardware2.jpg" alt="Alt text">
</div>


## Software Design Overview

The software is designed as a finite state machine. The main functionality of the project is in main.py with all other files supporting it.
The full overview of the software design is shown here:
[Github Pages](https://tristandelemos.github.io/ME405_TermProject/)



## Discussion of Results

A discussion of the results.  How did you test your system?  How well has your system performed in these tests?

The system worked perfectly the night before the true testing. On the day of the true testing, we were only able to hit one shot out of three.

A brief discussion of what you've learned about the project and recommendations for anyone who would like to build upon your work:

We would have the coders look deeper into tasks and see if that would make the system faster than it is now. We were unable to use taskshare and cotask because the system would not allow that much memory to be on the hardware. We would also look into the PID loop and see why the PID loop would not work correctly for us.

