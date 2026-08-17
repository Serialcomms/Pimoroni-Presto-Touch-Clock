# Pimoroni Presto - base support for display, wifi, ntp time and i2c

import secrets  # Your Wi-Fi credentials file

import sys
import time
import ntptime
import network
import machine
from touch import Button
from presto import Presto
from collections import namedtuple
from picovector import ANTIALIAS_FAST, PicoVector, Transform
machine.freq(270000000)   # overclock RP2350 from 150MHz to 270MHz for faster rendering

NTP_HOST = "uk.pool.ntp.org" # Preferred NTP server pool for the UK-based users
NTP_LAST_UPDATE_TIME = 0 

# Pimoroni Presto full resolution display configuration
presto  = Presto(full_res=True, ambient_light=False, layers=1, direct_to_fb=False)
display = presto.display
touch = presto.touch
vector = PicoVector(display)
WIDTH, HEIGHT = display.get_bounds()
display.set_pen(0)
display.clear()
presto.update()
vector.set_antialiasing(ANTIALIAS_FAST)
vector.set_font("Roboto-Medium.af", 48)
pico_rtc = machine.RTC()
usb_serial = machine.USBDevice()

# Named tuple definition for NTP date/time
date_time_ntp = namedtuple("date_time_ntp", [
    "year", "month", "day",
    "hour", "minute", "second",
    "weekday", "yearday"
])

# Named tuple definition for RTC date/time
date_time_rtc = namedtuple("date_time_rtc", [
    "year", "month", "day",
    "weekday", "hour", "minute",
    "second", "subseconds"
])

t = Transform()
vector.set_transform(t)

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(200, 200, 200)
LIGHT_GRAY = display.create_pen(40, 40, 40)
DARK_GREY = display.create_pen(100, 100, 100)
GRAY = display.create_pen(30, 30, 30)
GREY = display.create_pen(30, 30, 30)
RED = display.create_pen(220, 30, 30)   

RP2350_USBCTRL_REGS_BASE = 0x50110000
USBCTRL_SIE_STATUS = RP2350_USBCTRL_REGS_BASE + 0x050

def usb_is_suspended():
    status = machine.mem32[USBCTRL_SIE_STATUS]
    return bool(status & (1 << 4))

def usb_is_connected():
    status = machine.mem32[USBCTRL_SIE_STATUS]
    return bool(status & (1 << 16))

def usb_is_available():    
    active = usb_serial.active
    connected = usb_is_connected()
    suspended = usb_is_suspended()
    
    available = active and connected and not suspended
    
    return available

def usb_print(fmt, *args):
    """
    MicroPython printf-like function using variadic arguments
    Prints to USB only if USB connected and host is active / not sleeping,
    to prevent clock application from stalling if print fails
    
    :param fmt: Format string (supports % formatting or str.format style)
    :param args: Values to substitute into the format string
    """
    if usb_is_available() == True:
        
        try:
            output = fmt % args
            print(output)
            presto.set_led_rgb(6, 0, 32, 0)       # Set LED below USB-C connector to dim Green
        except (TypeError, ValueError) as e:
            presto.set_led_rgb(6, 200, 0, 0)      # Set LED below USB-C connector to Bright Red
            print("usb_printf - format error:", e)
            
    else:
        presto.set_led_rgb(6, 32, 18, 0),         # Set LED below USB-C connector to dark amber

def show_message(text, row): # startup messages before word clock runs

    display.set_pen(WHITE)
    vector.set_font("Roboto-Medium.af", 32)
    vector.text(f"{text}", 10, row * 40)
    presto.update()
    
    time.sleep(0.5)
    
def connect_to_wifi():
    
    presto.set_led_rgb(4, 32, 0, 0)      # Set LED closest to radio module to red until connected
    ssid = getattr(secrets, "WIFI_SSID", None)
    
    password = getattr(secrets, "WIFI_PASSWORD", None)

    if not ssid or not password:
        presto.set_led_rgb(4, 200, 0, 0) # Set LED closest to radio module to Bright Red  
        usb_print("ERROR: Wi-Fi credentials missing in secrets.py")
        return False

            # Using Pimoroni's built-in WiFi connection helper
    try:
            usb_available = usb_is_available()         
            print("Presto USB Serial Ready" if usb_available else "Presto USB Serial NOT Ready")
            usb_print("Connecting to %s using Presto library", ssid)          
            presto.connect()  # Automatically uses credentials from secrets.py
            usb_print("WiFi connected to %s via Presto helper", ssid)
            wlan = network.WLAN(network.STA_IF)
            PRESTO_WLAN_NETWORK = "WiFi Network = " + wlan.config('essid')
            PRESTO_IP_ADDRESS = "IP Address = " + wlan.ifconfig()[0]
            show_message(PRESTO_IP_ADDRESS, 2)
            show_message(PRESTO_WLAN_NETWORK, 3)
            usb_print(PRESTO_IP_ADDRESS)
            presto.set_led_rgb(4, 0, 32, 0)  # Set LED closest to radio module to Dim Green         
    
            return True
        
    except Exception as e:
            presto.set_led_rgb(4, 200, 0, 0) # Set LED closest to radio module to Bright Red  
            print(f"ERROR: Presto Wi-Fi connection failed: {e}")
            return False
        
def start_ntp_sync():
        
    global NTP_LAST_UPDATE_TIME
    
    """Sync Presto's RP2350 Real-Time Clock (RTC) with NTP Server (UTC)."""
    usb_print("Setting time from NTP Server Pool %s", NTP_HOST)
    
    try:     
        ntptime.host = NTP_HOST
        ntptime.settime()
        NTP_LAST_UPDATE_TIME = time.time()
        formatted_ntp_time = get_formatted_ntp_time()
        show_message("NTP Time = " + formatted_ntp_time, 5)
        usb_print("Presto Start NTP, Last Update %i", NTP_LAST_UPDATE_TIME)
    
        presto.set_led_rgb(3, 0, 32, 0)           # Set top-centre LED to dim green 
        
        return True
             
    except OSError:
        #machine.RTC().datetime((YYYY, MM, DD, weekday, HH, MM, SS, subseconds))
        pico_rtc.datetime((2026, 1, 1, 1, 18, 30, 0, 0)) # set default 1-Jan-2026 18:30:00
        show_message("ERROR setting time from NTP Server", 4)
        usb_print("ERROR: Unable to contact NTP server")
        presto.set_led_rgb(3, 200, 0, 0)          # Set top-centre LED to bright red
        
        return False
    
def update_ntp_time():
   
    global NTP_LAST_UPDATE_TIME
   
    try:
        """Sync RTC with NTP (UTC)."""
        ntptime.host = NTP_HOST
        ntptime.settime()
        NTP_LAST_UPDATE_TIME = time.time()
        presto.set_led_rgb(3, 0, 32, 0)           # Set top-centre LED to dim green
        usb_print("NTP Time Updated %i", NTP_LAST_UPDATE_TIME)
       
    except OSError:
        presto.set_led_rgb(3, 32, 18, 0),         # Set top-centre LED to dark amber
        usb_print("ERROR: Unable to contact NTP server")        


def _last_sunday(year, month):
    """Return the day number of the last Sunday of a given month."""
    # Check days 31 → 25 (all possible last Sundays)
    for day in range(31, 24, -1):
        try:
            if time.localtime(time.mktime((year, month, day, 0,0,0,0,0)))[6] == 6:
                return day
        except:
            pass
    return 31  # fallback (should never happen)

def _is_uk_daylight_saving_time():
    
    """Return True if UK/LONDON British Summer Time (BST) is active."""
    
    ntp_time = get_time_ntp()

    # Last Sunday in March at 01:00 UTC
    march_sunday = _last_sunday(ntp_time.year, 3)
    dst_start = time.mktime((ntp_time.year, 3, march_sunday, 1,0,0,0,0))

    # Last Sunday in October at 02:00 UTC
    oct_sunday = _last_sunday(ntp_time.year, 10)
    dst_end = time.mktime((ntp_time.year, 10, oct_sunday, 2,0,0,0,0))

    ntp_epoch_time = time.time()
    
    return dst_start <= ntp_epoch_time < dst_end

def get_time_ntp():
    
    """
    Get the current date/time from time.time() and return as DateTime struct.
    """
    try:
        epoch_seconds = time.time()  # Get current epoch time in seconds
        
        # Convert to tuple (year, month, mday, hour, minute, second, weekday, yearday)
        presto_time = time.localtime(epoch_seconds)
        
        return date_time_ntp(*presto_time)     # Populate named tuple
    
    except Exception as e:
        usb_print("Error getting time:", e)
        return None        

def get_time_rtc():
    
    try:
        
        local_realtime = pico_rtc.datetime()
        
        return date_time_rtc(*local_realtime)
    
    except Exception as e:
        usb_print("Error getting RTC time:", e)
        return None
    
    
def get_local_time(dst_adjust_seconds):
    
     try:
           
        epoch_seconds = time.time() + dst_adjust_seconds
        
        # Convert to tuple (year, month, mday, hour, minute, second, weekday, yearday)
        local_time_epoch = time.localtime(epoch_seconds)
        
        local_time = date_time_ntp(*local_time_epoch)
        
        return date_time_ntp(*local_time)
         
     except Exception as e:
        usb_print("Error getting local time:", e)
        return None
      
def get_formatted_ntp_time():
             
    ntp_time = get_time_ntp()
        
    if ntp_time:
 
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            ntp_time.year,
            ntp_time.month,
            ntp_time.day,
            ntp_time.hour,
            ntp_time.minute,
            ntp_time.second
        )
    
        return formatted_time
    
    else:
          
        return None   

def print_time_rtc():
    
    rtc_time = get_time_rtc()

    if rtc_time:
    
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            rtc_time.year,
            rtc_time.month,
            rtc_time.day,
            rtc_time.hour,
            rtc_time.minute,
            rtc_time.second
        )
     
        usb_print("Pico Real Time Clock: %s", formatted_time)
        
    else:
                    
        usb_print("ERROR: failed to read RTC time")        
    
def print_time_ntp():
    
    ntp_time = get_time_ntp()

    if ntp_time:
 
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            ntp_time.year,
            ntp_time.month,
            ntp_time.day,
            ntp_time.hour,
            ntp_time.minute,
            ntp_time.second
        )
            
        usb_print("Pico NTP Update Time: %s", formatted_time)
    
    else:
                
        usb_print("ERROR: failed to read NTP time")

def print_time_dst(dst_adjust_seconds):
    
     try:
           
        epoch_seconds = time.time() + dst_adjust_seconds
        
        # Convert to date_time_ntp tuple (year, month, mday, hour, minute, second, weekday, yearday)
        local_time_epoch = time.localtime(epoch_seconds)
        
        local_time = date_time_ntp(*local_time_epoch)
        
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            local_time.year,
            local_time.month,
            local_time.day,
            local_time.hour,
            local_time.minute,
            local_time.second
        )
        
        usb_print("Presto UK Local Time: %s", formatted_time)
        
     except Exception as e:
            
        usb_print("Error getting time:", e)
            
def print_next_ntp_update(update_seconds):

    try:
           
        epoch_seconds = time.time() + update_seconds
        
        # Convert to tuple (year, month, mday, hour, minute, second, weekday, yearday)
        next_ntp_epoch = time.localtime(epoch_seconds)
        
        local_time = date_time_ntp(*next_ntp_epoch)
        
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            local_time.year,
            local_time.month,
            local_time.day,
            local_time.hour,
            local_time.minute,
            local_time.second
        )
    
        usb_print("Next NTP Update Time: %s", formatted_time)
        
    except Exception as e:     
        usb_print("Error getting next NTP update time:", e)
        
