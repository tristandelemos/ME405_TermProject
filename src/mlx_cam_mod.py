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


    def get_bytes(self, array, limits=None):
        """!
        @brief   Generate a bytes object containing image data.
        @details This function generates a set of lines, each having one row of
                 image data in Comma Separated Variable format. The lines can
                 be printed or saved to a file using a @c for loop.
        @param   array The array of data to be presented
        @param   limits A 2-iterable containing the maximum and minimum values
                 to which the data should be scaled, or @c None for no scaling
        """
        if limits and len(limits) == 2:
            scale = (limits[1] - limits[0]) / 255#(max(array) - min(array))
            offset = 0#limits[0] - min(array)
        else:
            offset = 0.0
            scale = 1.0
            
        arr = bytearray(32*24)
        
        for n in range(len(arr)):
            pix = (array[n]*scale+offset)
            arr[n] = int(pix)
            
        return arr
    

    
    def calculate_centroid_bytes(self,ref_array, image_array, limit = 128):
        """!
        @brief   Calculates centroid from bytearray of points in image
        @details 
        @param   image_array A bytearray of image values in order starting at top left pixel
                 Lines are 32 long, there are 24 lines total
        @param   scalar A float value from (0 to 1) used to determine how high the image values need to be to be
                 considered a target
        @returns A tuple of x, y values of the centroid position"""

        x_array = bytearray()
        y_array = bytearray()

        x_val = 1
        y_val = 24

        num = 0

        # for byte in image_array:
        for i in range(len(image_array)):
            # if x_val == 33:
            #     x_val = 0
            #     y_val -= 1
            # if y_val == 0:
            #     print("shouldn't get here")
            #     break

            byte = image_array[i] - ref_array[i]
            #print(byte)
            if byte < 0:
                byte = 0

            x_val = i%32 + 1
            y_val = 24 - i//32
            
            if byte > (limit):
                #print(byte)
                x_array.append(x_val)
                y_array.append(y_val)
                num += 1
                


        x_sum = sum(x_array)
        y_sum = sum(y_array)

        print("num2:", num)

        if num > 0:
            cent_x = x_sum/num
            cent_y = y_sum/num
        else:
            return -1, -1
        
        return cent_x, cent_y


    def find_angle(self,ref_array, image_array, limit = 20):

        c_x2, c_y2 = self.calculate_centroid_bytes(ref_array, image_array, limit)
        
        if c_x2 < 0 or c_y2 < 0:
            return -60, -60

        #angle calculation
        cx = 32-c_x2
        if (cx) > 16:
            cx_f = cx-16
        else:
            cx_f = -1*(16-cx)
        if (c_y2) > 12:
            cy_f = c_y2-12
        else:
            cy_f = -1*(12-c_y2)
        
        #print(f"cx_f: {cx_f}, cy_f: {cy_f}")
        x_deg = cx_f * (55/32)
        y_deg = cy_f * (35/24)

        return x_deg, y_deg
        



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
    
    #ref = camera.get_image()
    #ref_array = camera.get_bytes(ref, (0, 99))
    ref_array =bytearray(b'\xea\xe6\xea\xe6\xe8\xe5\xe8\xe5\xe8\xe3\xe8\xe4\xe8\xe2\xe7\xe3\xe9\xe1\xe7\xe3\xe9\xe2\xe8\xe2\xe9\xe1\xe9\xe2\xe7\xe1\xea\xdf\xe7\xe5\xe3\xe2\xe6\xe5\xe2\xe2\xe5\xe3\xe2\xe1\xe5\xe2\xe1\xe0\xe5\xe1\xe1\xdf\xe6\xe1\xe3\xdf\xe6\xe1\xe3\xde\xe5\xe0\xe4\xdd\xe9\xe5\xe8\xe6\xe7\xe3\xe8\xe4\xe8\xe3\xe7\xe3\xe6\xe2\xe6\xe2\xe8\xe2\xe7\xe3\xe8\xe2\xe6\xe2\xe8\xe1\xe8\xe2\xe8\xe1\xe8\xdf\xe5\xe5\xe3\xe3\xe4\xe3\xe2\xe1\xe5\xe2\xe2\xe0\xe4\xe1\xe1\xdf\xe5\xe0\xe2\xdf\xe5\xe1\xe1\xdf\xe5\xe0\xe3\xdf\xe5\xe0\xe3\xdc\xe9\xe5\xe8\xe6\xe9\xe4\xe8\xe4\xe8\xe2\xe7\xe3\xe8\xe2\xe6\xe2\xe9\xe2\xe7\xe2\xe8\xe1\xe7\xe2\xe9\xe0\xe7\xe1\xe8\xe0\xe7\xde\xe6\xe4\xe1\xe1\xe6\xe2\xe1\xe0\xe5\xe1\xe1\xdf\xe5\xe1\xe1\xdf\xe6\xe1\xe1\xdf\xe5\xe1\xe2\xdf\xe6\xdf\xe3\xdf\xe5\xdf\xe3\xdc\xe9\xe5\xe7\xe5\xe7\xe4\xe7\xe4\xe7\xe3\xe7\xe3\xe6\xe1\xe7\xe2\xe8\xe2\xe7\xe2\xe7\xe1\xe6\xe2\xe8\xe1\xe8\xe1\xe8\xe0\xe8\xdf\xe5\xe3\xe1\xe1\xe4\xe3\xe0\xe0\xe3\xe1\xe1\xdf\xe3\xe0\xe0\xde\xe4\xe1\xe1\xde\xe4\xe0\xe1\xde\xe6\xdf\xe1\xde\xe5\xdf\xe3\xdb\xe8\xe6\xe7\xe5\xe7\xe3\xe7\xe4\xe7\xe2\xe6\xe3\xe5\xe2\xe6\xe2\xe7\xe1\xe6\xe2\xe6\xe1\xe7\xe2\xe8\xe0\xe7\xe1\xe8\xe0\xe8\xdf\xe4\xe2\xe0\xe1\xe2\xe1\xe1\xdf\xe3\xe0\xdf\xde\xe1\xe0\xdf\xde\xe4\xdf\xe0\xde\xe4\xdf\xe1\xde\xe5\xdf\xe0\xdd\xe5\xdf\xe2\xdc\xe9\xe5\xe7\xe5\xe8\xe4\xe7\xe4\xe7\xe2\xe5\xe2\xe6\xe1\xe6\xe2\xe7\xe1\xe7\xe2\xe8\xe1\xe7\xe2\xe8\xe0\xe6\xe1\xe6\xe0\xe7\xde\xe4\xe1\xdf\xe0\xe3\xe2\xe0\xdf\xe3\xe1\xdf\xde\xe2\xdf\xdf\xde\xe3\xde\xe0\xde\xe4\xdf\xe0\xdd\xe4\xde\xe0\xdd\xe3\xde\xe1\xdb\xe7\xe4\xe6\xe4\xe5\xe3\xe5\xe4\xe5\xe2\xe5\xe1\xe5\xe1\xe5\xe1\xe6\xe1\xe5\xe1\xe7\xe1\xe6\xe2\xe7\xe1\xe6\xe1\xe6\xdf\xe7\xdf\xe3\xe1\xde\xdf\xe1\xdf\xde\xde\xe1\xde\xde\xdc\xe0\xdf\xde\xdc\xe1\xde\xde\xdc\xe3\xde\xe0\xde\xe3\xde\xdf\xdc\xe3\xde\xe1\xda\xe5\xe5\xe5\xe5\xe6\xe3\xe6\xe3\xe5\xe1\xe4\xe1\xe5\xe1\xe5\xe1\xe6\xe1\xe5\xe1\xe6\xe1\xe6\xe1\xe7\xe0\xe6\xe1\xe5\xdf\xe7\xde\xe0\xe1\xdd\xde\xe1\xdf\xdd\xde\xe0\xde\xdc\xdc\xe0\xdd\xdd\xdc\xe1\xde\xdd\xdc\xe2\xde\xde\xdc\xe3\xde\xdf\xdc\xe2\xde\xe0\xda\xe5\xe4\xe5\xe4\xe5\xe2\xe4\xe1\xe5\xe0\xe3\xe1\xe5\xe0\xe3\xe0\xe6\xe0\xe5\xe1\xe5\xdf\xe5\xe1\xe6\xdf\xe5\xdf\xe5\xdf\xe5\xdd\xe0\xdf\xdc\xdd\xdf\xde\xdc\xdc\xdf\xde\xdc\xdb\xdf\xdd\xdc\xdb\xe1\xdd\xdd\xdb\xe1\xde\xdd\xdc\xe3\xdd\xde\xdb\xe1\xdd\xdf\xd9\xe3\xe3\xe4\xe3\xe3\xe1\xe4\xe1\xe3\xe0\xe4\xe1\xe3\xe0\xe4\xe0\xe3\xdf\xe5\xe1\xe4\xdf\xe5\xdf\xe5\xdf\xe4\xdf\xe5\xdf\xe6\xde\xdd\xde\xda\xdc\xde\xdd\xdb\xdc\xdd\xdc\xdb\xda\xde\xdc\xda\xdb\xdf\xdc\xdc\xda\xdf\xdc\xdc\xda\xe1\xdc\xdd\xda\xe1\xdc\xde\xd9\xe3\xe2\xe3\xe3\xe2\xe1\xe3\xe1\xe3\xe0\xe3\xe1\xe2\xe0\xe3\xe1\xe3\xdf\xe5\xe0\xe4\xdf\xe4\xe0\xe5\xdf\xe4\xdf\xe3\xde\xe5\xde\xdb\xdd\xd9\xdb\xdc\xdc\xda\xda\xdd\xdc\xda\xda\xdc\xdc\xda\xd9\xde\xdc\xdb\xd9\xde\xdc\xdb\xda\xe0\xda\xdc\xd9\xdf\xdc\xdc\xd8\xe2\xe2\xe2\xe3\xe2\xe1\xe3\xe1\xe2\xdf\xe1\xdf\xe1\xdf\xe2\xdf\xe4\xdf\xe3\xe0\xe4\xdf\xe3\xdf\xe3\xde\xe2\xdf\xe2\xde\xe2\xdd\xd7\xd9\xd4\xd7\xd8\xd9\xd5\xd6\xd8\xd8\xd5\xd6\xd8\xd7\xd6\xd5\xda\xd7\xd5\xd6\xda\xd7\xd6\xd5\xda\xd7\xd7\xd6\xda\xd8\xd9\xd4')
    #print(ref_array)
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
            c_x2, c_y2 = camera.calculate_centroid_bytes(ref_array, image_array, limit = 20)
            cbytestime = time.ticks_ms()
            


            #print(f"initial print time: {time.ticks_diff(print_time, new_start)}")
            #print(f"second print time: {time.ticks_diff(my_print_time, print_time)}")
            #print(f"centroid calc time: {time.ticks_diff(centroid_time, my_print_time)}")
            #print(f"total post-snap time: {time.ticks_diff(centroid_time, new_start)}")
            
            
            print(f"get bytes time: {time.ticks_diff(getbytestime, second_start)}")
            print(f"centroid 2 time: {time.ticks_diff(cbytestime, getbytestime)}")

            #print(f"\nCentroid: {c_x}, {c_y}")
            print(f"\nCentroid2: {c_x2}, {c_y2}")

            x_deg, y_deg = camera.find_angle(ref_array, image_array, limit = 20)

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
