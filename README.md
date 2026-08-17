### Hybrid Word / Vector Touch Clock application for Pimoroni Presto ###

A hybrid word (letter matrix) and vector (normal clock face) application in Micropython for the [Pimoroni Presto](https://pimoroni.com/presto)

Display runs in full anti-aliased 480 * 480 resolution with touch enabled for toggling between the word and vector clocks.

Uses WiFi to set time from an NTP server, with on-screen startup and IDE progress reporting. 

Both clocks update every second, the word clock displays in multiple colours for increased interest.

Ambient LEDs on back of Presto indicate WiFI, NTP and USB status. 3 white LEDs also change every second.

Most of the vector clock is from the [Pimoroni examples](https://github.com/pimoroni/presto) , the word clock was written locally by the repo owner.

Some supporting functions (as noted) written with AI help from Copilot.

Note - WiFi credentials need to be supplied in secrets.py

Potentially interesting project for both new and experienced Python developers.

Further 'Pythonic' improvements and enhancements can be made to this repo - please feel free to fork and 
update as required.
