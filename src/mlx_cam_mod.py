"""!
@file mlx_cam.py

RAW VERSION
This version uses a stripped down MLX90640 driver which produces only raw data,
not calibrated data, in order to save memory.

This file contains a wrapper that facilitates the use of a Melexis MLX90640
thermal infrared camera for general use. The wrapper contains a class MLX_Cam
whose use is greatly simplified in comparison to that of the base class,
@c class @c MLX90640, by mwerezak, who has a cool fox avatar, at
@c https://github.com/mwerezak/micropython-mlx90640

To use this code, upload the directory @c mlx90640 from mwerezak with all its
contents to the root directory of your MicroPython device, then copy this file
to the root directory of the MicroPython device.

There's some test code at the bottom of this file which serves as a beginning
example.

@author mwerezak Original files, Summer 2022
@author JR Ridgely Added simplified wrapper class @c MLX_Cam, January 2023
@author R Verleur Added byte array operations to improve speed
@author T Spicer Added functions to extract centroid/angle data from byte array
@copyright (c) 2022 by the authors and released under the GNU Public License,
    version 3.
"""

import gc
from array import array
import utime as time
from machine import Pin, I2C
from mlx90640 import MLX90640
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern


class MLX_Cam:
    """!
    @brief   Class which wraps an MLX90640 thermal infrared camera driver to
             make it easier to grab and use an image.
    """

    def __init__(self, i2c, address=0x33, pattern=InterleavedPattern,
                 width=NUM_COLS, height=NUM_ROWS):
        """!
        @brief   Set up an MLX90640 camera.
        @param   i2c An I2C bus which has been set up to talk to the camera;
                 this must be a bus object which has already been set up
        @param   address The address of the camera on the I2C bus (default 0x33)
        @param   pattern The way frames are interleaved, as we read only half
                 the pixels at a time (default ChessPattern)
        @param   width The width of the image in pixels; leave it at default
        @param   height The height of the image in pixels; leave it at default
        """
        ## The I2C bus to which the camera is attached
        self._i2c = i2c
        ## The address of the camera on the I2C bus
        self._addr = address
        ## The pattern for reading the camera, usually ChessPattern
        self._pattern = pattern
        ## The width of the image in pixels, which should be 32
        self._width = width
        ## The height of the image in pixels, which should be 24
        self._height = height

        # The MLX90640 object that does the work
        self._camera = MLX90640(i2c, address)
        self._camera.set_pattern(pattern)
        self._camera.setup()

        ## A local reference to the image object within the camera driver
        self._image = self._camera.raw


    def get_image(self):
        """!
        @brief   Get one image from a MLX90640 camera.
        @details Grab one image from the given camera and return it. Both
                 subframes (the odd checkerboard portions of the image) are
                 grabbed and combined (maybe; this is the raw version, so the
                 combination is sketchy and not fully tested). It is assumed
                 that the camera is in the ChessPattern (default) mode as it
                 probably should be.
        @returns A reference to the image object we've just filled with data
        """
        for subpage in (0, 1):
            while not self._camera.has_data:
                time.sleep_ms(50)
                print('.', end='')
            image = self._camera.read_image(subpage)

        return image


    def get_bytes(self, array):
        """!
        @brief   Generate a bytes object containing image data.
        @details This function generates a byte array, with each byte representing
                 a single pixel. By using a byte array we can get all the data at once
                 without running out of memory and operations can be performed much more
                 quickly
        @param   array The array of data to be presented
        @returns a bytearray of image pixel values (768 bytes)
        """
            # Offset the data because it comes in negative
            offset = 128
            scale = 1.0
        # Allocate memory for byte array to avoid allocating in a loop
        arr = bytearray(32*24)
        # Iterate through all elements in arr and replace each one with a
        #  value found from the input array
        for n in range(len(arr)):
            pix = (array[n]*scale+offset)
            arr[n] = int(pix)
            
        return arr
    

    
    def calculate_centroid_bytes(self,ref_array, image_array, limit = 128):
        """!
        @brief   Calculates centroid from bytearray of points in image
        @details calculates the centroid of the pixels above a limit value in the bytearray from image_array
                 also recieves a reference array of cold pixels to get rid of any variation caused by camera
        @param   ref_array A bytearray of image values for a cold wall in order starting at top left pixel 
        @param   image_array A bytearray of image values in order starting at top left pixel
                 Lines are 32 long, there are 24 lines total
        @param   limit A 8 bit integer value for the lower limit value the camera considers as a warm pixel
        @returns A tuple of x, y values of the centroid position"""

        # Declare arrays
        x_array = bytearray()
        y_array = bytearray()
        # Start points for the data
        x_val = 1
        y_val = 24
        # Number of pixels above the limit temp
        num = 0
        # Go through each element in the array and format by subtracting reference image
        for i in range(len(image_array)):
            byte = image_array[i] - (ref_array[i]-255)

            if byte < 0:
                byte = 0
            # Recover x and y index from array index
            x_val = i%32 + 1
            y_val = 24 - i//32
            # compare value to limit and if bigger add element number to x and y array
            if byte > (limit):
                #print(byte)
                x_array.append(x_val)
                y_array.append(y_val)
                num += 1
                

        # Sum elements in x and y arrays
        x_sum = sum(x_array)
        y_sum = sum(y_array)

        print("num:", num)
        
        # If some pixels were found calculate centroid
        if num > 0:
            cent_x = x_sum/num
            cent_y = y_sum/num
        # Otherwise return -1,-1 for an error state
        else:
            return -1, -1
        
        return cent_x, cent_y


    def find_angle(self,ref_array, image_array, limit = 20):
        """!
        @brief Calculates the angle in the cameras view cone
        @details Runs calculate centroid to find centerpoint then scales based on the
                 specified view angles of the camera (55 x 35 degrees)
        @param   ref_array A bytearray of image values for a cold wall in order starting at top left pixel 
        @param   image_array A bytearray of image values in order starting at top left pixel
                 Lines are 32 long, there are 24 lines total
                 @param   limit A 8 bit integer value for the lower limit value the camera considers as a warm pixel
        @returns A tuple of pitch yaw angles for movement of the gun  
        """
        # Calculate the centroid
        c_x2, c_y2 = self.calculate_centroid_bytes(ref_array, image_array, limit)
        # If error return an unreasonable value for error detection later
        if c_x2 < 0 or c_y2 < 0:
            return -60, -60
        
        # center reference the image
        cx = c_x2
        cx_f = cx-16
        cy_f = c_y2-12

        
        # Calculate angles based on view angle and resolution (assuming a linear scaling for both)
        x_deg = cx_f * (55/32)
        y_deg = cy_f * (35/24)
        
        # Return the angle
        return x_deg, y_deg
        #return y_deg,x_deg
        



# The test code sets up the sensor, then grabs and shows an image in a terminal
# every ten and a half seconds or so.
## @cond NO_DOXY don't document the test code in the driver documentation
if __name__ == "__main__":

    # The following import is only used to check if we have an STM32 board such
    # as a Pyboard or Nucleo; if not, use a different library
    gc.collect()

    print(f"free memory: {gc.mem_free()}")
    print(f"used memory: {gc.mem_alloc()}")
    
    try:
        from pyb import info

    # Oops, it's not an STM32; assume generic machine.I2C for ESP32 and others
    except ImportError:
        # For ESP32 38-pin cheapo board from NodeMCU, KeeYees, etc.
        i2c_bus = I2C(1, scl=Pin(22), sda=Pin(21))

    # OK, we do have an STM32, so just use the default pin assignments for I2C1
    else:
        i2c_bus = I2C(1)

    print("MXL90640 Easy(ish) Driver Test")

    # Select MLX90640 camera I2C address, normally 0x33, and check the bus
    i2c_address = 0x33
    scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
    print(f"I2C Scan: {scanhex}")

    # Create the camera object and set it up in default mode
    camera = MLX_Cam(i2c_bus)
    
    ref = camera.get_image()
    ref_array = camera.get_bytes(ref, (0, 99))
    #ref_array =bytearray(b'\xea\xe6\xea\xe8\xe8\xe5\xe8\xe6\xea\xe5\xea\xe5\xe8\xe2\xe7\xe3\xe8\xe1\xe8\xe3\xe8\xe1\xe7\xe2\xe8\xe1\xe8\xe2\xe7\xe0\xe9\xdf\xe7\xe4\xe3\xe3\xe5\xe4\xe3\xe1\xe6\xe3\xe3\xe2\xe4\xe1\xe1\xdf\xe5\xe0\xe1\xdf\xe5\xe0\xe1\xde\xe5\xe0\xe2\xde\xe4\xdf\xe3\xdc\xe8\xe5\xe9\xe6\xe7\xe5\xe8\xe5\xe8\xe4\xe8\xe5\xe7\xe3\xe8\xe3\xe8\xe2\xe8\xe2\xe7\xe1\xe7\xe2\xe7\xe0\xe7\xe1\xe8\xe0\xe8\xdf\xe5\xe4\xe3\xe3\xe3\xe4\xe2\xe1\xe4\xe2\xe2\xe1\xe4\xe2\xe1\xdf\xe5\xe1\xe1\xdf\xe4\xe0\xe1\xde\xe4\xdf\xe2\xde\xe5\xdf\xe2\xdc\xe9\xe5\xe9\xe6\xea\xe5\xe9\xe6\xe9\xe3\xe8\xe4\xea\xe3\xe8\xe3\xe9\xe2\xe7\xe3\xe8\xe1\xe7\xe2\xe7\xdf\xe7\xe1\xe6\xde\xe8\xdf\xe5\xe4\xe2\xe2\xe6\xe3\xe2\xe2\xe6\xe1\xe2\xe1\xe5\xe1\xe2\xdf\xe6\xe1\xe1\xdf\xe4\xdf\xe1\xde\xe5\xdf\xe1\xde\xe4\xde\xe2\xdb\xe8\xe5\xe7\xe5\xe7\xe4\xe8\xe4\xe7\xe2\xe8\xe5\xe7\xe3\xe6\xe3\xe7\xe1\xe8\xe3\xe6\xdf\xe5\xe1\xe8\xe0\xe7\xe1\xe6\xdf\xe8\xdf\xe3\xe1\xde\xdf\xe3\xe1\xe0\xdf\xe3\xe1\xe0\xdf\xe2\xe0\xdf\xde\xe3\xdf\xe1\xdd\xe1\xdc\xdc\xda\xe3\xde\xe0\xdc\xe3\xde\xe1\xda\xe8\xe5\xe8\xe7\xe7\xe4\xe8\xe5\xe7\xe3\xe8\xe6\xed\xea\xea\xe5\xe8\xe2\xe7\xe3\xe7\xe0\xe6\xe1\xe7\xdf\xe6\xe0\xe7\xde\xe8\xdf\xe3\xe2\xe0\xe1\xe2\xe1\xe0\xe0\xe2\xe0\xe0\xdf\xe5\xe3\xdf\xdf\xe4\xdf\xe0\xde\xe3\xde\xdf\xdd\xe3\xde\xe0\xdc\xe4\xde\xe2\xda\xe8\xe3\xe7\xe5\xe8\xe4\xe7\xe4\xe7\xe2\xe5\xe2\xe5\xe1\xe5\xe1\xe6\xe0\xe6\xe2\xe6\xdf\xe5\xe1\xe6\xdf\xe5\xe0\xe5\xde\xe7\xde\xe3\xe0\xdf\xdf\xe2\xe0\xdf\xde\xe2\xdf\xde\xde\xe0\xde\xde\xdc\xe1\xdd\xdf\xdc\xe3\xdd\xde\xdc\xe2\xdc\xde\xdc\xe1\xdc\xe1\xda\xe6\xe3\xe5\xe3\xe5\xe2\xe6\xe4\xe5\xe1\xe5\xe2\xe5\xe1\xe5\xe1\xe5\xe0\xe4\xe1\xe5\xdf\xe5\xe0\xe5\xde\xe5\xdf\xe6\xdf\xe8\xe0\xe1\xdf\xdc\xdd\xde\xde\xdd\xdd\xe0\xde\xdd\xdc\xdf\xdd\xde\xdb\xe0\xdc\xdd\xdb\xe1\xdc\xde\xdb\xe0\xdb\xde\xda\xe1\xde\xe1\xda\xe5\xe3\xe5\xe4\xe4\xe1\xe5\xe4\xe5\xe1\xe5\xe2\xe5\xe0\xe5\xe1\xe6\xdf\xe4\xe1\xe4\xdf\xe4\xe0\xe6\xde\xe4\xe0\xe5\xdf\xe8\xe0\xe1\xdf\xdc\xdc\xdf\xdd\xdc\xdc\xdf\xdd\xdc\xdb\xde\xdd\xdc\xda\xe0\xdc\xdc\xda\xdf\xdc\xdc\xda\xe1\xdc\xdc\xda\xe0\xdc\xe0\xda\xe5\xe3\xe5\xe4\xe4\xe1\xe4\xe3\xe5\xe1\xe4\xe1\xe5\xe0\xe4\xe1\xe6\xdf\xe4\xdf\xe4\xde\xe4\xdf\xe5\xde\xe4\xde\xe4\xde\xe6\xdf\xe1\xdf\xdb\xdc\xde\xde\xdb\xdb\xde\xdc\xdc\xda\xdf\xdc\xdb\xda\xe0\xdc\xdb\xd9\xdf\xda\xdb\xd9\xe0\xdb\xdc\xd9\xdf\xdc\xe0\xd9\xe2\xe2\xe4\xe3\xe3\xe1\xe3\xe2\xe3\xdf\xe4\xe1\xe3\xdf\xe4\xe2\xe3\xdf\xe3\xdf\xe3\xde\xe3\xdf\xe4\xde\xe4\xdf\xe5\xdf\xe7\xe0\xdd\xde\xda\xdc\xdd\xdc\xda\xda\xdd\xdb\xda\xd9\xdd\xdb\xdc\xdb\xde\xdb\xda\xd8\xde\xda\xdb\xd9\xdf\xda\xdb\xd9\xde\xdc\xdf\xda\xe2\xe3\xe3\xe3\xe3\xe1\xe3\xe2\xe3\xe0\xe4\xe2\xe3\xe0\xe4\xe2\xe4\xdf\xe4\xe0\xe4\xde\xe3\xe0\xe4\xde\xe3\xdf\xe3\xdf\xe7\xe2\xdc\xdd\xd8\xda\xdb\xdc\xd9\xda\xdc\xda\xd9\xd9\xdc\xda\xda\xd9\xdd\xda\xda\xd8\xdc\xda\xda\xd9\xde\xd9\xda\xd9\xdf\xdc\xde\xda\xe2\xe2\xe3\xe3\xe3\xe0\xe3\xe2\xe2\xdf\xe2\xe1\xe2\xdf\xe3\xe0\xe4\xdf\xe3\xe0\xe2\xde\xe3\xe0\xe3\xde\xe2\xdf\xe3\xdf\xe4\xe0\xd6\xd8\xd3\xd6\xd7\xd8\xd5\xd5\xd8\xd7\xd5\xd5\xd7\xd7\xd5\xd5\xd9\xd6\xd5\xd5\xd9\xd5\xd5\xd4\xd9\xd6\xd6\xd5\xd9\xd7\xd9\xd5')
    ref_array = bytearray(b'\xe9\xe5\xec\xea\xeb\xe7\xe9\xe6\xe8\xe3\xe8\xe5\xe7\xe2\xe6\xe3\xe7\xe1\xe7\xe2\xe7\xe0\xe7\xe1\xe8\xe1\xe8\xe2\xe7\xe1\xe9\xe0\xe5\xe5\xe3\xe3\xe8\xe6\xe2\xe2\xe5\xe3\xe2\xe0\xe5\xe1\xe0\xde\xe5\xe0\xe1\xde\xe5\xe0\xe1\xde\xe5\xe0\xe2\xde\xe5\xdf\xe4\xdc\xe7\xe3\xe8\xe6\xe7\xe6\xe9\xe5\xe7\xe3\xe8\xe4\xe6\xe2\xe7\xe3\xe7\xe1\xe5\xe2\xe7\xe0\xe6\xe1\xe6\xe0\xe6\xe1\xe7\xe0\xe8\xe0\xe4\xe3\xe1\xe2\xe3\xe2\xe3\xe1\xe4\xe3\xe1\xe0\xe4\xe2\xe1\xde\xe5\xdf\xe0\xde\xe4\xdf\xe1\xdd\xe5\xdf\xe1\xdd\xe5\xe0\xe3\xdc\xe6\xe3\xe5\xe4\xe7\xe3\xe7\xe5\xe9\xe3\xe8\xe5\xe8\xe3\xe8\xe3\xe7\xe1\xe4\xdf\xe5\xdf\xe6\xe1\xe8\xdf\xe7\xe1\xe7\xe0\xe7\xdf\xe3\xe1\xde\xdf\xe5\xe1\xe0\xdf\xe5\xe2\xe3\xe0\xe5\xe2\xe2\xdf\xe5\xdf\xdd\xda\xe2\xde\xdf\xdd\xe4\xdf\xe1\xde\xe4\xdf\xe2\xdb\xe4\xe1\xe5\xe3\xe5\xe2\xe6\xe3\xe6\xe1\xe8\xe5\xe7\xe3\xe7\xe3\xe7\xe1\xe6\xe1\xe6\xe0\xe5\xe0\xe6\xdf\xe7\xe1\xe6\xe0\xe8\xdf\xe1\xde\xdc\xdd\xe1\xe0\xdf\xde\xe2\xdf\xe0\xdf\xe3\xe0\xdf\xdd\xe3\xe0\xe0\xdc\xe3\xdf\xdf\xdc\xe4\xde\xe0\xdc\xe4\xde\xe2\xda\xe4\xe1\xe3\xe1\xe1\xe0\xe5\xe3\xe4\xe0\xe5\xe2\xe6\xe3\xe6\xe2\xe6\xdf\xe6\xe1\xe5\xdf\xe5\xe0\xe6\xdf\xe5\xe0\xe7\xdf\xe7\xdf\xdf\xde\xdc\xdc\xdc\xde\xde\xde\xe0\xde\xdd\xdd\xe1\xe0\xe0\xdc\xe2\xde\xdf\xdd\xe3\xde\xde\xdc\xe3\xde\xdf\xdc\xe4\xde\xe1\xda\xe5\xe1\xe3\xe1\xe2\xe1\xe5\xe3\xe4\xe0\xe4\xe0\xe5\xe0\xe4\xe1\xe6\xdf\xe6\xe1\xe5\xdf\xe5\xe0\xe6\xde\xe5\xe0\xe5\xde\xe7\xde\xdf\xde\xdb\xdb\xde\xde\xde\xdd\xe0\xdc\xdc\xdc\xdf\xde\xdd\xdb\xe1\xdd\xde\xdb\xe2\xde\xde\xdc\xe2\xdd\xde\xdc\xe1\xdc\xe0\xd9\xe6\xe3\xe4\xe3\xe1\xe0\xe4\xe1\xe3\xdf\xe3\xe1\xe3\xe0\xe4\xe0\xe5\xdf\xe4\xe0\xe5\xdf\xe5\xe1\xe5\xde\xe6\xe0\xe5\xde\xe6\xdf\xe0\xde\xdd\xde\xdf\xde\xdc\xdc\xdf\xdc\xdb\xda\xdf\xdd\xdd\xda\xdf\xdc\xdb\xda\xe1\xdd\xde\xdb\xe1\xdc\xde\xda\xe2\xdc\xdf\xd9\xe3\xe1\xe4\xe3\xe4\xe1\xe4\xe3\xe4\xe1\xe3\xe0\xe4\xde\xe3\xe0\xe4\xdf\xe3\xdf\xe4\xdf\xe4\xe0\xe5\xdf\xe4\xdf\xe4\xde\xe6\xde\xdc\xdc\xdb\xda\xde\xdd\xdb\xdb\xdf\xdd\xda\xda\xde\xdc\xdb\xda\xdf\xdc\xdb\xda\xe0\xdc\xdc\xda\xe1\xdd\xdd\xda\xdf\xdc\xde\xd8\xe3\xe1\xe5\xe3\xe3\xe0\xe2\xe0\xe2\xdf\xe2\xdf\xe3\xdf\xe3\xdf\xe4\xde\xe3\xdf\xe3\xde\xe3\xdf\xe4\xdd\xe4\xde\xe4\xde\xe5\xdc\xdc\xdc\xda\xdb\xdc\xdc\xd9\xd8\xdd\xdb\xd9\xd8\xdd\xdb\xda\xd9\xde\xdb\xda\xd9\xdf\xdb\xdb\xd9\xe0\xdb\xdc\xd9\xe0\xdc\xde\xd7\xe1\xe2\xe2\xe2\xe2\xdf\xe2\xe0\xe1\xde\xe3\xdf\xe3\xe1\xe5\xe0\xe2\xde\xe2\xdf\xe3\xde\xe3\xdf\xe4\xdd\xe3\xde\xe4\xde\xe5\xde\xdb\xdd\xd9\xda\xdc\xda\xd9\xd8\xdb\xda\xd9\xd8\xdd\xdf\xde\xda\xdd\xda\xda\xd9\xdd\xdb\xda\xd8\xdf\xda\xdb\xd8\xdf\xdb\xdc\xd8\xe1\xe1\xe1\xe0\xe0\xde\xe3\xe0\xe0\xde\xe1\xdf\xe3\xe1\xe5\xe1\xe2\xde\xe3\xde\xe2\xde\xe2\xdf\xe4\xdd\xe3\xde\xe1\xde\xe4\xde\xda\xdb\xd6\xd8\xd9\xda\xd7\xd7\xda\xd9\xd7\xd6\xdc\xdc\xdc\xda\xdc\xd9\xd9\xd7\xdb\xda\xd9\xd6\xde\xd9\xd9\xd7\xdd\xda\xdb\xd6\xe1\xe1\xe0\xe1\xe0\xdf\xe1\xdf\xdf\xdd\xde\xdc\xdf\xde\xe1\xde\xe2\xdc\xe0\xde\xe1\xde\xe2\xde\xe2\xdd\xe1\xde\xe1\xde\xe2\xdc\xd5\xd7\xd3\xd4\xd5\xd7\xd2\xd3\xd6\xd4\xd1\xd1\xd5\xd5\xd4\xd2\xd7\xd5\xd2\xd2\xd8\xd5\xd4\xd2\xd8\xd6\xd5\xd3\xd8\xd6\xd7\xd2')
    print(ref_array)
    while True:
        try:
            # Get and image and see how long it takes to grab that image
            print("Click.", end='')
            begintime = time.ticks_ms()
            image = camera.get_image()
            print(f" {time.ticks_diff(time.ticks_ms(), begintime)} ms")
            del begintime

            new_start = time.ticks_ms()

            print_time = time.ticks_ms()
                    
            
            my_print_time = time.ticks_ms()

            # c_x, c_y = calculate_centroid(cleared_image)
            #c_x, c_y = calculate_centroid(camera, image)

            centroid_time = time.ticks_ms()

            second_start = time.ticks_ms()
            image_array = camera.get_bytes(image)
            getbytestime = time.ticks_ms()
            c_x2, c_y2 = camera.calculate_centroid_bytes(ref_array, image_array, limit = 100)
            cbytestime = time.ticks_ms()
            


            #print(f"initial print time: {time.ticks_diff(print_time, new_start)}")
            #print(f"second print time: {time.ticks_diff(my_print_time, print_time)}")
            #print(f"centroid calc time: {time.ticks_diff(centroid_time, my_print_time)}")
            #print(f"total post-snap time: {time.ticks_diff(centroid_time, new_start)}")
            
            
            print(f"get bytes time: {time.ticks_diff(getbytestime, second_start)}")
            print(f"centroid 2 time: {time.ticks_diff(cbytestime, getbytestime)}")

            #print(f"\nCentroid: {c_x}, {c_y}")
            print(f"\nCentroid2: {c_x2}, {c_y2}")

            x_deg, y_deg = camera.find_angle(ref_array, image_array, limit = 100)

            print(f"found angle: {x_deg}, {y_deg}")


            
            cont = input("continue? y or n ")
            if cont == "n":
                break
            else:
                time.sleep_ms(1000)
            # time.sleep_ms(5000)

        except KeyboardInterrupt:
            break

    print ("Done.")

## @endcond End the block which Doxygen should ignore
