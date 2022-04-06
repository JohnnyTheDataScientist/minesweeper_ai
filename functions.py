import win32api, win32con, win32gui
import ctypes
import pygetwindow as gw
from PIL import Image, ImageGrab
import cv2
import numpy as np
import pandas as pd
import pyautogui
from functions import *
import time
from random import randrange


### need this code to get the correct coordinate for win32api.GetCursorPos()
user32 = ctypes.windll.user32 
user32.SetProcessDPIAware()

def obtain_window_info():
    # Minesweeper X is the name of the Window    
    minesweeper_window = gw.getWindowsWithTitle('Minesweeper X')[0]
    window_size = minesweeper_window.size
    window_top_left = minesweeper_window.topleft
    return window_size, window_top_left

def take_snippet(window_size,  window_top_left):    
    tile_cord = (round(window_top_left[0]),
            round(window_top_left[1]),
            round(window_top_left[0] + window_size[0]),
            round(window_top_left[1] + window_size[1])
           )
    im = ImageGrab.grab(bbox = tile_cord)
    im.save('game_snippets/temp.png')
    im = cv2.imread("./game_snippets/temp.png")
    return im

def convert_to_numbers(im):
    # first identify the size of the map (height x width)
    tiles_top_index = 127 # pixel 128
    tiles_left_index = 19 # pixel 20
    tiles_right_index = im.shape[1] - 20
    tiles_bottom_index = im.shape[0] - 19
    np_tiles = im[tiles_top_index : tiles_bottom_index, tiles_left_index:tiles_right_index, :]
    height = int((np_tiles.shape[0] + 1)/20)
    width = int((np_tiles.shape[1] + 1)/20)
    
    # calculate the average pixel values for each tile
    tile_middle_mean = np.zeros([height, width, 3])
    tile_top_edge_mean = np.zeros([height, width, 3])
    for i in range(height):
        for j in range(width):
            ### pixel positions for each tile
            top = 20 * i
            bottom = top + 19
            left = 20 * j
            right = left + 19

            for k in range(3):
                tile_top_edge_mean[i,j, k] = np.mean(np_tiles[top, left:right, k])

            ### trim the edge pixels
            top = top + 2
            bottom = bottom - 2
            left = left + 2
            right = right - 2

            for k in range(3):
                tile_middle_mean[i,j, k] = np.mean(np_tiles[top:bottom, left:right, k])
                
    # convert it to numbers
    ### color channel: BGR
    middle_pixel_mean = np.array([[1,210,138,138], [2,103,162,103],
                                   [3,107,107,220], [4,167,117,117],
                                   [5,96,96,160], [6,159,159,94],
                                   [7,132,132,132],
                                   [9,195,195,195], 
                                   [11,143,143,173], [12,94,94,94],
                                   [13,7,7,122],  [14,74,74,143]])

    top_edge_pixel_mean = np.array([[0,130,130,130], [9,253,253,253]])
    
    # 9 --- unrevealed 
    # 10 -- edge padding
    # 11 -- flag
    # 12 -- mine
    # 13 -- stepped_mine
    # 14 -- wrong_flag    

    tile_number = np.ones([height, width])
    tile_number = tile_number * 8
    for i in range(height):
        for j in range(width):
            for k in range(middle_pixel_mean.shape[0]):     
                if (tile_middle_mean[i,j,0] > middle_pixel_mean[k, 1] - 5) & \
                (tile_middle_mean[i,j,0] < middle_pixel_mean[k, 1] + 5) & \
                (tile_middle_mean[i,j,1] > middle_pixel_mean[k, 2] - 5) & \
                (tile_middle_mean[i,j,1] < middle_pixel_mean[k, 2] + 5) & \
                (tile_middle_mean[i,j,2] > middle_pixel_mean[k, 3] - 5) & \
                (tile_middle_mean[i,j,2] < middle_pixel_mean[k, 3] + 5):
                    tile_number[i,j] = middle_pixel_mean[k, 0]

    for i in range(height):
        for j in range(width):                                
            if tile_number[i,j] == 9:
                for l in range(top_edge_pixel_mean.shape[0]):
                    if (tile_top_edge_mean[i,j,0] > top_edge_pixel_mean[l, 1] - 20) & \
                    (tile_top_edge_mean[i,j,0] < top_edge_pixel_mean[l, 1] + 20) & \
                    (tile_top_edge_mean[i,j,1] > top_edge_pixel_mean[l, 2] - 20) & \
                    (tile_top_edge_mean[i,j,1] < top_edge_pixel_mean[l, 2] + 20) & \
                    (tile_top_edge_mean[i,j,2] > top_edge_pixel_mean[l, 3] - 20) & \
                    (tile_top_edge_mean[i,j,2] < top_edge_pixel_mean[l, 3] + 20):
                        tile_number[i,j] = top_edge_pixel_mean[l, 0]
    
    # pad the surrounding with zeros
    tile_number = np.pad(tile_number, ((1, 1), (1, 1)), 'constant', constant_values=(10))
    return tile_number

def tile_pixel_position(height, width, window_top_left):
    pixel_height = window_top_left[1] + 127 + 10 + (20 * (height-1))
    pixel_width = window_top_left[0] + 19 +10 + (20 * (width-1))
    return(pixel_width, pixel_height)

def initialized():
    window_size, window_top_left = obtain_window_info()
    reset_botton = (window_top_left[0] + window_size[0]/2, window_top_left[1] + 94)
    pyautogui.click(reset_botton)
    pyautogui.click(reset_botton)
    im = take_snippet(window_size,  window_top_left)
    tile_number = convert_to_numbers(im)
    solved = np.zeros([tile_number.shape[0], tile_number.shape[1]])
    solved[tile_number == 10] = 1
    solved[tile_number == 0] = 1

    # initialize by randomly click on the map
    unrevealed_tile = np.where(tile_number == 9)
    random_index = randrange(0, len(unrevealed_tile[0]))
    pixel_width, pixel_height = tile_pixel_position(unrevealed_tile[0][random_index], 
                                                   unrevealed_tile[1][random_index],
                                                   window_top_left
                                                  )
    pyautogui.click(pixel_width, pixel_height)
    return solved
    
    
def simply_rule(solved):
    window_size, window_top_left = obtain_window_info()
    im = take_snippet(window_size,  window_top_left)
    tile_number = convert_to_numbers(im)
    number_of_solved_tiles_new = len(np.where(solved == 1)[0])
    number_of_solved_tiles_old = 0
    
    # while we are still updating
    while number_of_solved_tiles_old != number_of_solved_tiles_new:
        number_of_solved_tiles_old = number_of_solved_tiles_new

        # loop through each unsolved tile
        unsolved_index = np.where(solved == 0)
        for i in range(len(unsolved_index[0])):
            # If the tile number is between 1 and 8, check its surrounding tiles
            # and see if the number of flags and the number of unrevealed tiles are the 
            # same as the number.
            target_number = tile_number[unsolved_index[0][i], unsolved_index[1][i]]
            if (target_number > 0) & (target_number <= 8):
                # find out the positon of the 3x3 square to look into
                square = tile_number[unsolved_index[0][i]-1:unsolved_index[0][i]+2,
                                    unsolved_index[1][i]-1:unsolved_index[1][i]+2
                                   ]
                number_of_flag = len(np.where(square == 11)[0])
                number_of_unrevealed = len(np.where(square == 9)[0])
                if number_of_flag + number_of_unrevealed == target_number:
                    ### right click on all unrevealed tiles and update the solved array
                    unrevealed_positions = [np.where(square == 9)[0] + unsolved_index[0][i] - 1, 
                                          np.where(square == 9)[1] + unsolved_index[1][i] - 1]
                    for j in range(len(unrevealed_positions[0])):
                        height = unrevealed_positions[0][j]
                        width = unrevealed_positions[1][j]
                        pixel_width, pixel_height = tile_pixel_position(height, width, window_top_left)
                        pyautogui.click(pixel_width, pixel_height, button='right')
                    im = take_snippet(window_size,  window_top_left)
                    tile_number = convert_to_numbers(im)
                    solved[unsolved_index[0][i], unsolved_index[1][i]] = 1
                    solved[tile_number == 0] = 1
                    solved[tile_number == 11] = 1

                if number_of_flag == target_number:
                    ### left click on all unrevealed tiles and update the solved array
                    unrevealed_positions = [np.where(square == 9)[0] + unsolved_index[0][i] - 1, 
                                          np.where(square == 9)[1] + unsolved_index[1][i] - 1]
                    for j in range(len(unrevealed_positions[0])):
                        height = unrevealed_positions[0][j]
                        width = unrevealed_positions[1][j]
                        pixel_width, pixel_height = tile_pixel_position(height, width, window_top_left)
                        pyautogui.click(pixel_width, pixel_height, button='left')
                    im = take_snippet(window_size,  window_top_left)
                    tile_number = convert_to_numbers(im)
                    solved[unsolved_index[0][i], unsolved_index[1][i]] = 1
                    solved[tile_number == 0] = 1
                    solved[tile_number == 11] = 1
        number_of_solved_tiles_new = len(np.where(solved == 1)[0])
    return solved

def random_click():
    window_size, window_top_left = obtain_window_info()
    im = take_snippet(window_size,  window_top_left)
    tile_number = convert_to_numbers(im)
    unrevealed_tile = np.where(tile_number == 9)
    random_index = randrange(0, len(unrevealed_tile[0]))
    pixel_width, pixel_height = tile_pixel_position(unrevealed_tile[0][random_index], 
                                                   unrevealed_tile[1][random_index],
                                                   window_top_left
                                                  )
    pyautogui.click(pixel_width, pixel_height)

def check_step_bomb():
    window_size, window_top_left = obtain_window_info()
    im = take_snippet(window_size,  window_top_left)
    tile_number = convert_to_numbers(im)
    return 13 in tile_number

def check_complete():
    window_size, window_top_left = obtain_window_info()
    im = take_snippet(window_size,  window_top_left)
    tile_number = convert_to_numbers(im)
    return not (9 in tile_number)

def check_status():
    ## status = 0 ---- game in progress
    ## status = 1 ---- game complete
    ## status = 2 ---- game failed
    status = 0
    window_size, window_top_left = obtain_window_info()
    im = take_snippet(window_size,  window_top_left)
    face_snippet = im[88:100, int(window_size[0]/2 - 6) : int(window_size[0]/2 + 7), :]
    value_mean = np.mean(face_snippet)
    if (value_mean >= 102) & (value_mean <= 106):
        status = 1
    if (value_mean >= 136) & (value_mean <= 140):
        status = 2
    return status