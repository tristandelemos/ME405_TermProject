# Created by Tristan de Lemos, Trenten Spicer, and Rees Verleur
#
# main file for Turret Term Project


import utime


S0_INIT = 0
S1_TAKE_PICTURE = 1
S2_MOVE_MOTORS = 2
S3_SHOOT = 3
S4_PAUSE = 4




def main():
    
    state = S0_INIT
    
    while(True):
        
        try:
            # Initialize motors, servo, and camera
            if(state == S0_INIT):
            
            
                state = S1_TAKE_PICTURE
            
            
            # Take picture and find warmest area to shoot at
            if(state == S1_TAKE_PICTURE):
            
        
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