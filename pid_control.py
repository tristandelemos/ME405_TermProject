"""!@file pid_control.py
        This file contains the class which allows for proportional-
        integral-derivative control of the motor. The class contains
        an initializer and 5 methods: run, set_setpoint, set_Kp,
        set_Ki, and set_Kd
"""
class PidControl:
    """!@brief	This class performs proportional control
        @details	This class performs proportional control
                    specifically for the motor position on the
                    motors in the ME_405 kit
    """
    def __init__(self, Kp = 1, Ki = 0, Kd = 0, setpoint = 0):
        """!@brief	The constructor for the motor driver class
        @details	The constructor takes in initial settings for
                    gain and setpoint. For a step response the setpoint
                    should start at 0 and will later be changed by the
                    set_setpoint method
        @param	Kp The proportional gain for the control loop
        @param	Ki The integral gain for the control loop
        @param	Kd The derivative gain for the control loop
        @param	setpoint The initial setpoint for the control loop
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.err = 0
        self.esum = 0
        self.elast = 0
        self.dele = 0
        self.effort = 0
        
    def run(self,position):
        """!@brief	Runs the control loop
        @details	Executes one step of the control loop and
                    returns the effort
        @param	position The current position of the system
        """
        # Calculate current error from setpoint
        self.err = position-self.setpoint
        # Add current error to error sum (integral)
        self.esum += self.err
        # Calculate change from last error (derivative)
        self.dele = self.err-self.elast
        # Save current error as last error for next run through loop
        self.elast = self.err
        # Calculate effort as linear combination of proportional, integral, and derivative controls
        self.effort = self.Kp*self.err+self.Ki*self.esum+self.Kd*self.dele
        return self.effort
        
    def set_setpoint(self, new_setpoint):
        """!@brief	Changes the setpoint for the system
        @details	Adjusts the setpoint for the control loop
                    for a step response this should be changed once
        @param	new_setpoint The desired setpoint for the system
        """
        self.setpoint = new_setpoint
    def set_Kp(self, new_gain):
        """!@brief	Changes the proportional gain
        @details	Adjusts the proportional gain for the control
                    loop.
        @param	new_gain The desired gain for the system
        """
        self.Kp = new_gain
    def set_Ki(self, new_gain):
        """!@brief	Changes the integral gain
        @details	Adjusts the integral gain for the control
                    loop.
        @param	new_gain The desired gain for the system
        """
        self.Ki = new_gain
    def set_Kd(self, new_gain):
        """!@brief	Changes the derivative gain
        @details	Adjusts the derivative gain for the control
                    loop.
        @param	new_gain The desired gain for the system
        """
        self.Kd = new_gain
        
    