"""!@file motor_reader.py
        This file sends the required setpoint and gain to the nucleo over a 
        serial communication. The sent data works with motor_controller.py to
        control the motor using the pro_control.py file.
"""
import serial
from matplotlib import pyplot
import time


def main():
   """!@brief This is the main function which passes data to the micropython
      device. 
       @details This function uses the pyserial module to communicate over the
       serial port to the micropython. The function sends a setpoint and gain
       to the Nucleo and waits for the return data which represents the motor
       response. The data is then plotted and displayed.
   """
    
   m1_x_list = []
   m1_y_list = []
   m2_x_list = []
   m2_y_list = []

   with serial.Serial('COM4', 115200,timeout = 3) as s_port:
       #
       # send ready statement
       s_port.write(b'ready\r\n')
       
       while True:
           sline = s_port.readline()
           print(sline)
           if sline==b'end\r\n':
               break
        
           try:
                motor, data1, data2 = sline.split(b',')
                data2 = data2.split(b'\r')[0]
                d1stat, d2stat = True, True
                
                try:
                    data1 = float(data1)
                except (ValueError):
                    d1stat = False
                    print("Data in column 1 is corrupt")
                
                try:
                    data2 = float(data2)
                except(ValueError):
                    d2stat = False
                    print("Data in column 2 is corrupt")

                if (d1stat and d2stat):
                    if motor == b'motor 1':
                        m1_x_list.append(data1)
                        m1_y_list.append(data2)
                    elif motor == b'motor 2':
                        m2_x_list.append(data1)
                        m2_y_list.append(data2)
           except:
                # line not formatted correctly
                print("list is not in the expected format")
                
            
            
       pyplot.plot(m1_x_list, m1_y_list, 'go-',label="Motor_1")
       pyplot.plot(m2_x_list, m2_y_list, 'ro-',label="Motor_2")
       pyplot.xlabel("Time [ms]")
       pyplot.ylabel("Position [enc counts]")
       pyplot.legend()
       pyplot.show()
            
        #for i in range(len(x_list)):
        #    print(x_list[i], ",", y_list[i])




if __name__ == "__main__":
    main()