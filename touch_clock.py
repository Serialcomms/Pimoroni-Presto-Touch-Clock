# ICON schedule
# NAME Touch Clock
# DESC Touch Clock in Colour

import gc
import time
import random
import network
import machine
import ntptime
import presto_base

from presto import Presto
from touch import Button
from picovector import ANTIALIAS_FAST, ANTIALIAS_X16, PicoVector, Transform, Polygon

from presto_base import touch
from presto_base import vector
from presto_base import presto
from presto_base import display
from presto_base import show_message
from presto_base import update_ntp_time
from presto_base import usb_print
from presto_base import get_time_rtc
from presto_base import get_time_ntp
from presto_base import get_local_time
from presto_base import get_formatted_ntp_time
from presto_base import print_time_rtc
from presto_base import print_time_ntp
from presto_base import print_time_dst
from presto_base import start_ntp_sync
from presto_base import print_next_ntp_update
from presto_base import _is_uk_daylight_saving_time
from presto_base import WIDTH, HEIGHT
from presto_base import BLACK, WHITE, LIGHT_GRAY, GRAY, GREY, RED

t = Transform()
vector = PicoVector(display)
vector.set_transform(t)

rtc = machine.RTC()
ntp_time_string = None
formatted_time = None
next_ntp_update_time = 0
current_time = 0
current_year = 0
current_day = 0
current_month = 0
current_hours = 0
current_minutes = 0
current_seconds = 0
clock_tick_tock = 0
rows, cols = 11, 11

BUTTON_WIDTH = 460
BUTTON_HEIGHT = 460

SCREEN_BUTTON = False
ANALOGUE = False

# Vector clock items from Pimoroni Examples - see Pimoroni MIT License
# https://github.com/pimoroni/presto/blob/main/examples/vector_clock_full.py

MIDDLE = (int(WIDTH / 2), int(HEIGHT / 2))

hub = Polygon() # small red circle over second hand
hub.circle(int(WIDTH / 2), int(HEIGHT / 2), 5)

face = Polygon()
face.circle(int(WIDTH / 2), int(HEIGHT / 2), int(HEIGHT / 2))

tick_mark = Polygon()
tick_mark.rectangle(int(WIDTH / 2) - 3, 10, 6, int(HEIGHT / 48))

hour_mark = Polygon()
hour_mark.rectangle(int(WIDTH / 2) - 5, 10, 10, int(HEIGHT / 10))

minute_hand_length = int(HEIGHT / 2) - int(HEIGHT / 24) - 2
minute_hand_width = int(HEIGHT / 16)
minute_hand = Polygon()
minute_hand.path((-5, -minute_hand_length), (-10, minute_hand_width), (10, minute_hand_width), (5, -minute_hand_length))

hour_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8) - 2
hour_hand_width = int(HEIGHT / 16)
hour_hand = Polygon()
hour_hand.path((-5, -hour_hand_length), (-10, hour_hand_width), (10, hour_hand_width), (5, -hour_hand_length))

second_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8) - 2
second_hand_width = int(HEIGHT / 8)
second_hand = Polygon()
second_hand.path((-2, -second_hand_length), (-2, second_hand_width), (2, second_hand_width), (2, -second_hand_length))

button_full_screen = Button(0, 0, WIDTH - 1, HEIGHT - 1)

CLOCK_WORD_COLOURS = [
    
    display.create_pen(200, 0, 0),         # red
    display.create_pen(254, 215, 0),       # gold
    display.create_pen(128, 0, 0),         # maroon
    display.create_pen(0, 0, 200),         # navy
    display.create_pen(0, 128, 128),       # teal
    display.create_pen(250, 165, 30),      # orange
    display.create_pen(220, 215, 55),      # yellow
    display.create_pen(0, 128, 40),        # green
    display.create_pen(255, 0, 255),       # magenta
    display.create_pen(0, 255, 255),       # cyan
    display.create_pen(0, 255, 0),         # lime
    display.create_pen(40, 64, 140),       # blue
    display.create_pen(100, 40, 110),      # purple
    display.create_pen(250, 100, 180),     # pink
    display.create_pen(220, 30, 30),       # red
    display.create_pen(100, 200, 250),     # light blue
    display.create_pen(200, 200, 200)      # white
   
]

grid_letters = [
    
    ['i', 't' , 'r', 'i' , 's' , 'P' , 'a' , 'f' , 't' , 'e' , 'r' ] , # it is, after          (P)
    ['n', 'e' , 'a', 'r' , 'l' , 'y' , 'R' , 'n' , 'o' , 'w' , 'E' ] , # nearly, now           (R, E)
    ['t', 'w' , 'e', 'n' , 't' , 'y' , 'J' , 'f' , 'i' , 'v' , 'e' ] , # twenty, (twenty-five) 
    ['q', 'u' , 'a', 'r' , 't' , 'e' , 'r' , 'h' , 'a' , 'l' , 'f' ] , # quarter, half        
    ['t', 'e' , 'n', 'S' , 't' , 'o' , 'T' , 'p' , 'a' , 's' , 't' ] , # ten, to, past         (S, T)
    ['O', 'n' , 'e', 'T' , 'w' , 'o' , 'T' , 'h' , 'r' , 'e' , 'e' ] , # One, Two, Three        
    ['F', 'o' , 'u', 'r' , 'F' , 'i' , 'v' , 'e' , 'S' , 'i' , 'x' ] , # Four, Five, Six 
    ['S', 'e' , 'v', 'e' , 'n' , 'O' , 'E' , 'i' , 'g' , 'h' , 't' ] , # Seven, Eight          (O)
    ['N', 'i' , 'n', 'e' , 'x' , 'E' , 'l' , 'e' , 'v' , 'e' , 'n' ] , # Nine, Eleven
    ['T', 'e' , 'n', 'O' , 'P' , 'T' , 'w' , 'e' , 'l' , 'v' , 'e' ] , # Ten, Twelve
    ['N', 'o' , 'o', 'n' , 'O' , 'Z' , 'C' , 'l' , 'o' , 'c' , 'k' ]   # Noon, O'Clock
    
    # filler letters include those from the word PRESTO
    # J and Z are used for symbols - and '   
]

grid_letter_colours = [ 
    [4, 4, 0, 5, 5, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] ,
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ] 
]

def update_clock_time():
    
    global current_hours
    global current_minutes
    global current_seconds
    global clock_tick_tock
        
    london_dst = _is_uk_daylight_saving_time()

    if london_dst == True:
    
        usb_print("Clock Timezone: British Summer Time (BST)")
        local_time = get_local_time(3600)
        print_next_ntp_update(3600 + 3613)
        print_time_dst(3600)
        print_time_rtc()
        print_time_ntp()

    else:

        usb_print("Clock Timezone: Greenwich Mean Time (GMT)")
        local_time = get_local_time(0)
        print_next_ntp_update(3613)
        print_time_dst(0)
        print_time_rtc()
        print_time_ntp()
     
    current_hours = local_time.hour
    current_minutes = local_time.minute
    current_seconds = local_time.second
    
    clock_tick_tock ^= 1  # XOR with 1 flips the bit
    
    if clock_tick_tock == 1:
                   
        presto.set_led_rgb(0, 0, 0, 0) 
        presto.set_led_rgb(1, 32, 32, 32) 
        presto.set_led_rgb(2, 0, 0, 0) 
    
    else:
       
        presto.set_led_rgb(0, 32, 32, 32) 
        presto.set_led_rgb(1, 0, 0, 0) 
        presto.set_led_rgb(2, 32, 32, 32)
        
    NTP_TIME_NOW = time.time()
        
    NTP_DELTA = NTP_TIME_NOW - presto_base.NTP_LAST_UPDATE_TIME

    usb_print("NTP Update Delta = %i (update in %i seconds)", NTP_DELTA, 3613 - NTP_DELTA)
    
    if NTP_DELTA >= 3613:     
        update_ntp_time()      
        
         
# Function to search for a word in a 2D character grid (row-wise only)
# written with assistance from copilot
def match_word_in_grid(word, grid):
    """
    Searches for a word in a 2D grid of characters (row-wise).
    Returns (True, row_index, col_index, length) if found,
    otherwise (False, None, None, None).
    """
    if not isinstance(word, str):
        raise ValueError("Word must be a string")
    if not isinstance(grid, (list, tuple)):
        raise ValueError("Grid must be a list or tuple of lists/tuples")

    word_len = len(word)

    for row_idx, row in enumerate(grid):
        if not isinstance(row, (list, tuple)):
            raise ValueError("Each row must be a list or tuple of characters")
 
        row_str = "".join(row)        # Join row into a string for easier searching
        col_idx = row_str.find(word)  # Find the starting index of the word in the row
        if col_idx != -1:
            return True, row_idx, col_idx, word_len

    return False, None, None, None

def match_clock_word(clock_word, word_colour):
    
    found, row, col, length = match_word_in_grid(clock_word, grid_letters)

    if found:
        for grid_column in range(col, col + length):
            grid_letter_colours[row][grid_column] = word_colour
    else:
        usb_print("No word match found for %s", clock_word)
           
def clock_minutes_to(minutes_to):
    
    minutes_to_colour = minutes_to % len(CLOCK_WORD_COLOURS)
    
    if minutes_to_colour == 0:
        minutes_to_colour = len(CLOCK_WORD_COLOURS) - 1
        
    pen_colour = CLOCK_WORD_COLOURS[minutes_to_colour]
        
    if minutes_to < 33:    
        match_clock_word("after", minutes_to_colour)
        match_clock_word("half", minutes_to_colour)
        match_clock_word("past", minutes_to_colour)
        
    elif minutes_to < 35:
        match_clock_word("nearly", minutes_to_colour)
        match_clock_word("twentyJfive", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to == 35:
        match_clock_word("now", minutes_to_colour)
        match_clock_word("twentyJfive", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 37:
        match_clock_word("after", minutes_to_colour)
        match_clock_word("twentyJfive", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 40:
        match_clock_word("nearly", minutes_to_colour)
        match_clock_word("twenty", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to == 40:
        match_clock_word("now", minutes_to_colour)
        match_clock_word("twenty", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 43:
        match_clock_word("after", minutes_to_colour)
        match_clock_word("twenty", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 45:
        match_clock_word("nearly", minutes_to_colour)
        match_clock_word("quarter", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to == 45:
        match_clock_word("now", minutes_to_colour)
        match_clock_word("quarter", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 47:
        match_clock_word("after", minutes_to_colour)
        match_clock_word("quarter", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)    
        
    elif minutes_to < 50:
        match_clock_word("nearly", minutes_to_colour)
        match_clock_word("ten", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to == 50:
        match_clock_word("now", minutes_to_colour)
        match_clock_word("ten", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 53:
        match_clock_word("after", minutes_to_colour)
        match_clock_word("ten", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)        
        
    elif minutes_to < 55:
        match_clock_word("nearly", minutes_to_colour)
        match_clock_word("five", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to == 55:
        match_clock_word("now", minutes_to_colour)
        match_clock_word("five", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    elif minutes_to < 57:
        match_clock_word("after", minutes_to_colour)
        match_clock_word("five", minutes_to_colour)
        match_clock_word("to", minutes_to_colour)
        
    else:    
        match_clock_word("nearly", minutes_to_colour)
        match_clock_word("OZClock", minutes_to_colour)

def clock_minutes_past(minutes_past):
     
    global current_hours
    
    minutes_past_colour = minutes_past % len(CLOCK_WORD_COLOURS)
    
    if minutes_past_colour == 0:
        minutes_past_colour = len(CLOCK_WORD_COLOURS) - 1
    
    pen_colour = CLOCK_WORD_COLOURS[minutes_past_colour]
      
    if minutes_past < 3:
        match_clock_word("after", minutes_past_colour)
        match_clock_word("OZClock", minutes_past_colour)    # displays as O'Clock
    
    elif minutes_past < 5:
        match_clock_word("nearly", minutes_past_colour)
        match_clock_word("five", minutes_past_colour)       # lower case five
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past == 5:
        match_clock_word("now", minutes_past_colour)
        match_clock_word("five", minutes_past_colour)       # lower case five
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 7:
        match_clock_word("after", minutes_past_colour) 
        match_clock_word("five", minutes_past_colour)       # lower case ten
        match_clock_word("past", minutes_past_colour)    
        
    elif minutes_past < 10:
        match_clock_word("nearly", minutes_past_colour)
        match_clock_word("ten", minutes_past_colour)        # lower case ten
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past == 10:
        match_clock_word("now", minutes_past_colour)
        match_clock_word("ten", minutes_past_colour)        # lower case ten
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 12:
        match_clock_word("after", minutes_past_colour) 
        match_clock_word("ten", minutes_past_colour)        # lower case ten
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 15:
        match_clock_word("nearly", minutes_past_colour)
        match_clock_word("quarter", minutes_past_colour) 
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past == 15:
        match_clock_word("now", minutes_past_colour)
        match_clock_word("quarter", minutes_past_colour) 
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 17:
        match_clock_word("after", minutes_past_colour) 
        match_clock_word("quarter", minutes_past_colour) 
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 20:
        match_clock_word("nearly", minutes_past_colour)
        match_clock_word("twenty", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past == 20:
        match_clock_word("now", minutes_past_colour)
        match_clock_word("twenty", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 23:
        match_clock_word("after", minutes_past_colour) 
        match_clock_word("twenty", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 25:
        match_clock_word("nearly", minutes_past_colour)
        match_clock_word("twentyJfive", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past == 25:
        match_clock_word("now", minutes_past_colour)
        match_clock_word("twentyJfive", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 27:
        match_clock_word("after", minutes_past_colour) 
        match_clock_word("twentyJfive", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past < 30:
        match_clock_word("nearly", minutes_past_colour)
        match_clock_word("half", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    elif minutes_past == 30:
        match_clock_word("now", minutes_past_colour)
        match_clock_word("half", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        
    else:
        match_clock_word("after", minutes_past_colour)
        match_clock_word("half", minutes_past_colour)
        match_clock_word("past", minutes_past_colour)
        

def clock_time_to_words(clock_hours, clock_minutes):
    
    hour_words = {0: "Twelve", 1: "One", 2: "Two",
            3: "Three", 4: "Four", 5: "Five", 6: "Six",
            7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
            11: "Eleven", 12: "Twelve"}
    
    hours = clock_hours % 12
    minutes = clock_minutes
    
    this_hour_colour = (hours) % len(CLOCK_WORD_COLOURS)      
    next_hour_colour = (hours + 1) % len(CLOCK_WORD_COLOURS)
    
    if this_hour_colour == 0:
        this_hour_colour = len(CLOCK_WORD_COLOURS) - 1
        
    if next_hour_colour == 0:
        next_hour_colour = len(CLOCK_WORD_COLOURS) - 1        
     
    if minutes == 0:
        
        if clock_hours == 0:
            match_clock_word("Twelve", 5)
            match_clock_word("Noon" , 5)    
        else:    
            match_clock_word("now", 5)
            match_clock_word(hour_words[hours], 5)
            match_clock_word("OZClock", 5)  # displays as O'Clock
                          
    elif minutes < 33:  # minutes past the current hour
         match_clock_word(hour_words[hours], CLOCK_WORD_COLOURS[this_hour_colour])
         clock_minutes_past(clock_minutes)    
  
    else:               # minutes to the next hour
        match_clock_word(hour_words[hours + 1], CLOCK_WORD_COLOURS[next_hour_colour])
        clock_minutes_to(clock_minutes)
        
def clear_grid_colours():
    
    global clock_tick_tock
    
    old_tick_colour = grid_letter_colours[0][0]
    old_tock_colour = grid_letter_colours[0][3]
                
    for grid_row in range(0, 11):
        for grid_col in range(0, 11):
           grid_letter_colours[grid_row][grid_col] = 0
           
    new_random_colour = random.randint(1, len(CLOCK_WORD_COLOURS) - 1)
    while new_random_colour in (old_tick_colour, old_tock_colour):
        new_random_colour = random.randint(1, len(CLOCK_WORD_COLOURS) - 1)
                  
    if clock_tick_tock == 1:
                   
        grid_letter_colours[0][0] = new_random_colour
        grid_letter_colours[0][1] = new_random_colour
        
        grid_letter_colours[0][3] = old_tock_colour
        grid_letter_colours[0][4] = old_tock_colour
            
        #presto.speaker.play_tone(1500, 0.05)
        
    else:
                
        grid_letter_colours[0][0] = old_tick_colour
        grid_letter_colours[0][1] = old_tick_colour
        
        grid_letter_colours[0][3] = new_random_colour
        grid_letter_colours[0][4] = new_random_colour
        
def draw_grid():
   
    display.set_pen(BLACK)   # Clear the screen
    display.clear()

    default_x = 35
    x = default_x
    y = 16

    line_space = 40
    letter_space = 40
    margin = 24
    spacing = 4
           
    for letter_row in range(0, 11):
        
        x = margin
        y += letter_space
        
        for letter_col in range(0, 11):
            grid_colour = grid_letter_colours[letter_row][letter_col]
            clock_letter = grid_letters[letter_row][letter_col]
            
            letter_colour = CLOCK_WORD_COLOURS[grid_colour % len(CLOCK_WORD_COLOURS) - 1]
                    
            if grid_colour == 0:          # greyed-out characters
                
                display.set_pen(GRAY)  
                
                if clock_letter == "i":
                    vector.text(clock_letter.upper(), x + 6, y) # centre-align letter I in grid
                elif clock_letter == "w":
                    vector.text(clock_letter.upper(), x - 6, y) # centre-align letter W in grid 
                else:
                    vector.text(clock_letter.upper(), x, y)
                    
            else:
                                
                display.set_pen(letter_colour)
                
                if clock_letter == 'Z':
                    vector.text("'", x, y)
                elif clock_letter == 'J':
                    vector.text("-", x, y)                
                elif clock_letter == "i":
                    vector.text(clock_letter, x + 6, y) # centre-align letter i in grid
                elif clock_letter == "l":
                    vector.text(clock_letter, x + 6, y) # centre-align letter l in grid
                elif clock_letter == "w":
                    vector.text(clock_letter, x - 6, y) # centre-align letter w in grid 
                else:
                    vector.text(clock_letter, x, y)  
                    
            x += letter_space
                        
def show_vector_clock():
    
    # Vector clock from Pimoroni Examples - see Pimoroni MIT License
    # https://github.com/pimoroni/presto/blob/main/examples/vector_clock_full.py
    
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    vector.draw(face)
      
    vector.set_antialiasing(ANTIALIAS_X16)
    
    presto.set_backlight(0.5)
    
    t.reset()

    display.set_pen(GREY)

    for a in range(60):
        t.rotate(360 / 60.0 * a, MIDDLE)
        t.translate(0, 2)
        vector.draw(tick_mark)
        t.reset()

    for a in range(12):
        t.rotate(360 / 12.0 * a, MIDDLE)
        t.translate(0, 2)
        vector.draw(hour_mark)
        t.reset()

    display.set_pen(GREY)

    x, y = MIDDLE
    y += 5

    angle_minute = current_minutes * 6
    angle_minute += current_seconds / 10.0
    t.rotate(angle_minute, MIDDLE)
    t.translate(x, y)
    vector.draw(minute_hand)
    t.reset()

    angle_hour = (current_hours % 12) * 30
    angle_hour += current_minutes / 2
    t.rotate(angle_hour, MIDDLE)
    t.translate(x, y)
    vector.draw(hour_hand)
    t.reset()

    angle_second = current_seconds * 6
    t.rotate(angle_second, MIDDLE)
    t.translate(x, y)
    vector.draw(second_hand)
    t.reset()

    display.set_pen(BLACK)

    for a in range(60):
        t.rotate(360 / 60.0 * a, MIDDLE)
        vector.draw(tick_mark)
        t.reset()

    for a in range(12):
        t.rotate(360 / 12.0 * a, MIDDLE)
        vector.draw(hour_mark)
        t.reset()

    x, y = MIDDLE

    t.rotate(angle_minute, MIDDLE)
    t.translate(x, y)
    vector.draw(minute_hand)
    t.reset()

    t.rotate(angle_hour, MIDDLE)
    t.translate(x, y)
    vector.draw(hour_hand)
    t.reset()

    display.set_pen(RED)

    t.rotate(angle_second, MIDDLE)
    t.translate(x, y)
    vector.draw(second_hand)
    t.reset()

    vector.draw(hub)

    presto.update()
    gc.collect()

def show_word_clock():
    
    global screenshot
    
    global current_hours
    global current_minutes
    
    vector.set_font("cherry-hq.af", 60)
    
    presto.set_backlight(0.75)
    
    clock_time_to_words(current_hours, current_minutes)
        
    draw_grid()
    
    clear_grid_colours()
                     
    presto.update()
    
    gc.collect()
       
def run_presto_clock():
        
    try:
    
        while True:
        
            update_clock_time()
        
            touch_screen_check()
                   
            if ANALOGUE == True:
                show_vector_clock()
    
            else:
                show_word_clock()
            
    except KeyboardInterrupt:
            usb_print("Keyboard Interrupt Ctrl+C detected. Cleaning up...")

    finally:
            
            usb_print("Presto Word exited cleanly.")  
            presto.set_led_rgb(0, 0, 0, 0)       
            presto.set_led_rgb(1, 0, 0, 0)      
            presto.set_led_rgb(2, 0, 0, 0)    
            presto.set_led_rgb(3, 0, 0, 0)       
            presto.set_led_rgb(4, 0, 0, 0)      
            presto.set_led_rgb(5, 0, 0, 0)
            presto.set_led_rgb(6, 0, 0, 0)
            
            raise SystemExit
                  
def touch_screen_check():
    
    global ANALOGUE
     
    timestamp = time.time()
    
    while timestamp == time.time():
     
        touch.poll()
    
        if button_full_screen.is_pressed():
            
            ANALOGUE = not ANALOGUE
            
            if ANALOGUE:
                usb_print("Screen Touch, Clock = Analogue")
            else:
                usb_print("Screen Touch, Clock = Word")
            
            break

def show_error_and_wait(text, row):
    
    global SCREEN_BUTTON
    SCREEN_BUTTON = False
    
    display.set_pen(RED)
    vector.set_font("Roboto-Medium.af", 32)
    vector.text(f"{text}", 10, row * 40)
    presto.update()
        
    while SCREEN_BUTTON == False:       
        touch.poll()
        if button_full_screen.is_pressed():
            SCREEN_BUTTON = True
            
def set_startup_leds():
    
    presto.set_led_rgb(0, 0, 0, 0)
    presto.set_led_rgb(1, 0, 0, 0)
    presto.set_led_rgb(2, 0, 0, 0)
    presto.set_led_rgb(3, 32, 0, 0)
    presto.set_led_rgb(4, 32, 0, 0)
    presto.set_led_rgb(5, 0, 0, 0)
    presto.set_led_rgb(6, 32, 0, 0)
    
def set_error_leds():

    presto.set_led_rgb(0, 200, 0, 0)
    presto.set_led_rgb(1, 200, 0, 0)
    presto.set_led_rgb(2, 200, 0, 0)
    presto.set_led_rgb(3, 200, 0, 0)
    presto.set_led_rgb(4, 200, 0, 0)
    presto.set_led_rgb(5, 200, 0, 0)
    presto.set_led_rgb(6, 200, 0, 0)


# ================== [ Presto Touch Clock Startup ] =====================================            

set_startup_leds()

formatted_ntp_time = get_formatted_ntp_time()
usb_print("Presto startup NTP time = %s", formatted_ntp_time)

show_message("Presto Touch Clock Startup" , 1)

wifi_connected = presto_base.connect_to_wifi()

if wifi_connected:
     
     ntp_sync = start_ntp_sync()
     
     if ntp_sync == True:
            
         usb_print("Starting Presto Colour Touch Clock")
         show_message("Starting Presto Colour Touch Clock", 7)
         gc.collect()
         run_presto_clock()
     
     else:
         
         set_error_leds() 
         show_message("Unable to set time from NTP", 7)
         show_error_and_wait("Touch screen to soft reset to REPL", 9)
         machine.soft_reset()
         
else:
    
    set_error_leds()
    show_message("No Wifi connection", 6)
    show_error_and_wait("Touch screen to soft reset to REPL", 9)
    machine.soft_reset()
   
