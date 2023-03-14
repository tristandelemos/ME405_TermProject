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


    def get_csv(self, array, limits=None):
        """!
        @brief   Generate a string containing image data in CSV format.
        @details This function generates a set of lines, each having one row of
                 image data in Comma Separated Variable format. The lines can
                 be printed or saved to a file using a @c for loop.
        @param   array The array of data to be presented
        @param   limits A 2-iterable containing the maximum and minimum values
                 to which the data should be scaled, or @c None for no scaling
        """
        if limits and len(limits) == 2:
            scale = (limits[1] - limits[0]) / (max(array) - min(array))
            offset = limits[0] - min(array)
        else:
            offset = 0.0
            scale = 1.0
        for row in range(self._height):
            line = ""
            for col in range(self._width):
                pix = int((array[row * self._width + (self._width - col - 1)]
                          + offset) * scale)
                if col:
                    line += ","
                line += f"{pix}"
            yield line
        return


    def get_bytes(self, array, limits=None):
        """!
        @brief   Generate a bytes object containing image data.
        @details This function returns a bytes object containing the values
                 for all the pixels in the camera.
        @param   array The array of data to be presented
        @param   limits A 2-iterable containing the maximum and minimum values
                 to which the data should be scaled, or @c None for no scaling
        """
        if limits and len(limits) == 2:
            scale = (limits[1] - limits[0]) / (max(array) - min(array))
            offset = limits[0] - min(array)
        else:
            offset = 0.0
            scale = 1.0
            
        arr = bytearray(32*24)
        
        for n in range(len(arr)):
            pix = int((array[n]+ offset) * scale)
            arr[n] = pix
            
        return arr
    

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


def calculate_centroid(camera, image):
    """!
    @brief   Calculates centroid from image
    @details Loops through csv formatted image, takes high values and calculates
             the centroid from it. csv_image would optimally be pre-filtered to
             eliminate outliers
    @param   csv_image The thermal image file in csv format
    @returns A tuple of x, y values of the centroid position"""
    # image = csv_image

    # x_list = []
    # y_list = []

    #x_array = bytearray(b'\x00')

    x_array = array("B")
    y_array = array("B")

    y = 24
    num = 0

    for line in camera.get_csv(image, limits=(0, 99)):
        line_list = line.split(",")
        for i in range(len(line_list)):
            if int(line_list[i]) >= 50:
                # x_list.append(i)
                # y_list.append(y)
                x_array.append(i)
                y_array.append(y)
                #x_array[num] = i
                #y_array[num] = y
                num += 1
                
        y -= 1
        
    x_sum = sum(x_array)
    del x_array
    
    y_sum = sum(y_array)
    del y_array
    
    print("num1:", num)

    if num > 0:
        centroid_x = x_sum/num
        centroid_y = y_sum/num
    else:
        return -1, -1

    return centroid_x, centroid_y



def calculate_centroid_bytes(ref_array, image_array, upper=99, scalar=0.8):
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
        
        if byte > (upper * scalar):
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

    while True:
        try:
            # Get and image and see how long it takes to grab that image
            print("Click.", end='')
            begintime = time.ticks_ms()
            image = camera.get_image()
            print(f" {time.ticks_diff(time.ticks_ms(), begintime)} ms")
            del begintime

            new_start = time.ticks_ms()

            # Can show image.v_ir, image.alpha, or image.buf; image.v_ir best?
            # Display pixellated grayscale or numbers in CSV format; the CSV
            # could also be written to a file. Spreadsheets, Matlab(tm), or
            # CPython can read CSV and make a decent false-color heat plot.
            # cleared_image = []
            show_image = False
            show_csv = False
            if show_image:
                camera.ascii_image(image.buf)
            elif show_csv:
                for line in camera.get_csv(image, limits=(0, 99)):
                    # cleared_image.append(line)
                    print(line)
            else:
                # camera.ascii_art(image.v_ir)
                pass
                
                # for line in camera.get_csv(image.v_ir, limits=(0, 99)):
                #     cleared_image.append(line)
                    # time.sleep_ms(1)

            print_time = time.ticks_ms()
                    
            # time.sleep_ms(5000)
            print()
            
            # cleared_image.reverse()
            # y = 24
            # for line in cleared_image:
            #     linelist = line.split(",")
            #     newline = ""
            #     for i in range(len(linelist)):
            #         #print(f"line[i]: {line[i]}")
            #         if (int(linelist[i]) < 40):
            #             linelist[i] = "0"
            #             newline += "--"
            #         elif (int(linelist[i]) < 50):
            #             newline += "++"
            #         else:
            #             newline += "&&"
                        
            #     # newline = ",".join(linelist)
            #     if y > 9:
            #         print(y, newline)
            #     else:
            #         print(y, " " + newline)
            #     y -= 1

            # print(y, " 0102030405060708091011121314151617181920212223242526272829303132")
            
            my_print_time = time.ticks_ms()

            # c_x, c_y = calculate_centroid(cleared_image)
            c_x, c_y = calculate_centroid(camera, image)

            centroid_time = time.ticks_ms()

            second_start = time.ticks_ms()
            image_array = camera.get_bytes(image, limits=(0, 99))
            getbytestime = time.ticks_ms()
            c_x2, c_y2 = calculate_centroid_bytes(ref_array, image_array, upper=99, scalar=0.3)
            cbytestime = time.ticks_ms()
            


            #print(f"initial print time: {time.ticks_diff(print_time, new_start)}")
            #print(f"second print time: {time.ticks_diff(my_print_time, print_time)}")
            #print(f"centroid calc time: {time.ticks_diff(centroid_time, my_print_time)}")
            #print(f"total post-snap time: {time.ticks_diff(centroid_time, new_start)}")
            
            
            print(f"get bytes time: {time.ticks_diff(getbytestime, second_start)}")
            print(f"centroid 2 time: {time.ticks_diff(cbytestime, getbytestime)}")

            print(f"\nCentroid: {c_x}, {c_y}")
            print(f"\nCentroid2: {c_x2}, {c_y2}")
            
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
