"""!@file pro_control.py
        This file contains the class which allows for proportional
        control of the motor. The class contains an initializer and
        3 methods: run, set_setpoint, and set_Kp
"""
class ProControl:
    """!@brief	This class performs proportional control
        @details	This class performs proportional control
                    specifically for the motor position on the
                    motors in the ME_405 kit
    """
    def __init__(self, gain = 1, setpoint = 0):
        """!@brief	The constructor for the motor driver class
        @details	The constructor takes in initial settings for
                    gain and setpoint. For a step response the setpoint
                    should start at 0 and will later be changed by the
                    set_setpoint method
        @param	gain The initial gain for the proportional control loop
        @param	setpoint The initial setpoint for the control loop
        """
        self.gain = gain
        self.setpoint = setpoint
        
    def run(self,position):
        """!@brief	Runs the control loop
        @details	Executes one step of the control loop and
                    returns the effort
        @param	position The current position of the system
        """
        effort = self.gain*(position-self.setpoint)
        return effort
    def set_setpoint(self, new_setpoint):
        """!@brief	Changes the setpoint for the system
        @details	Adjusts the setpoint for the control loop
                    for a step response this should be changed once
        @param	new_setpoint The desired setpoint for the system
        """
        self.setpoint = new_setpoint
    def set_Kp(self, new_gain):
        """!@brief	Changes the gain for the system
        @details	Adjusts the proportional gain for the control
                    loop.
        @param	new_gain The desired gain for the system
        """
        self.gain = new_gain
        
    