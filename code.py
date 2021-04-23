"""
This is a work in progress!!!

This lets a circuitpython device play and skip tracks on an ipod using the Apple Accessory Protocol.
The code is pretty messy but it does (kind of) work.

KNOWN ISSUES:
    For some reason, play/pause only plays and only works once.
    I dont know how to calculate the checksum yet so it is hardcoded

Resources used:
    http://www.ipodlinux.org/Apple_Accessory_Protocol/
    https://www.instructables.com/Simple-Ipod-Controller/

Other things to note:
    iPod doc conector must have pin 11 (serial GND pin) connected to MC GND
    iPod doc conector must have pin 13 connected to MC TX
    iPod doc conector must have pin 21 must be pulled down to GND via a 550kOhm resistor.
        Note: most online resources say 500kOhm but I have found that actual devices using AAP use 550kOhm and that seems to work more reliably.
"""
import time
import board
from digitalio import DigitalInOut, Direction, Pull
import busio

playButton = DigitalInOut(board.BUTTON_A)
skipButton = DigitalInOut(board.BUTTON_B)

playButton.direction = Direction.INPUT
skipButton.direction = Direction.INPUT

playButton.pull = Pull.DOWN
skipButton.pull = Pull.DOWN

debug = False
# There apears to be some discrepency between the iPod linux wiki and a leaked official Apple doc on the AAP
# The iPod linux wiki gives the message format as:
# ---------------------------------------------------------------------------
# | field    | size | value                                                 |
# ---------------------------------------------------------------------------
# | header   |  2   | 0xff 0x55                                             |
# | length   |  1   | size of mode + command + param                        |
# | mode     |  1   | the mode the command is referring to                  |
# | command  |  2   | the two byte command                                  |
# | params   | 0-n  | optional parameter, depending on the command          |
# | checksum |  1   | 0x100 - ((len + mode + command + param bytes) & 0xFF) |
# ---------------------------------------------------------------------------
# The leaked Apple doc states that the message format is: (pg 63)
# -------------------------------------------------
# | Byte number | Value | Meaning                 |
# -------------------------------------------------
# | 0x00        | 0xFF  | Sync byte               |
# | 0x01        | 0x55  | Packet start byte       |
# | 0x02        | 0xNN  | Packet payload length   |
# | 0x03        | 0xNN  | Lingo ID                |
# | 0x04        | 0xNN  | Command ID              |
# | 0x05...0xNN | 0xNN  | Command data            |
# | (last byte) | 0xNN  | Packet payload checksum |
# ------------------------------------------------

# Udate: There is no discrepency between each table
# In the iPod linux table, "the mode the command is referring to" is the Lingo ID.
msg = [] #msg format [Sync, Start, Len, Mode, Command, Param, Checksum]
msg.append(bytes([0xFF])) # Sync Byte. Always include
msg.append(bytes([0x55])) # Packet start byte. Always include

uart = busio.UART(board.TX, rx=None, bits=8, parity=None, stop=1, baudrate=19200) #8N1

time_ran = 0
while True:
    if time_ran == 0:
        time_ran = 1
        # This puts the iPod into simple remote mode
        # FF 55 3 0 1 2 FA
        msg.append(bytes([0x03])) # Packet Payload Length
        msg.append(bytes([0x00])) # Lingo ID for General Lingo
        msg.append(bytes([0x01])) # First command byte
        msg.append(bytes([0x02])) # Second command byte
        msg.append(bytes([0xFA])) # Checksum
        # this sends the bytes to the iPod
        for i in range(0, 7):
            if debug:
                print(msg[i], ' ')
            else:
                uart.write(msg[i])
    if playButton.value:
        # sends the play command
        #print('playButton')
        # FF 55 3 2 0 1 FA 
        msg[3] = bytes([0x02])
        msg[4] = bytes([0x00])
        msg[5] = bytes([0x01])
        for i in range(0, 7):
            if debug:
                print(msg[i], ' ')
            else:
                uart.write(msg[i])
        # The release button command
        # FF 55 3 2 0 0 FB
        msg[5] = bytes([0x00])
        msg[6] = bytes([0xFB])
        for i in range(0, 7):
            if debug:
                print(msg[i], ' ')
            else:
                uart.write(msg[i])
        if debug:
            print('\n')
    if skipButton.value:
        # sends the skip button command
        #print('skipButton')
        # FF 55 3 2 0 8 F3 
        msg[3] = bytes([0x02])
        msg[4] = bytes([0x00])
        msg[5] = bytes([0x08])
        msg[6] = bytes([0xF3])
        for i in range(0, 7):
            if debug:
                print(msg[i], ' ')
            else:
                uart.write(msg[i])
        # sends the release button command
        # FF 55 3 2 0 0 FB
        msg[5] = bytes([0x00])
        msg[6] = bytes([0xFB])
        for i in range(0, 7):
            if debug:
                print(msg[i], ' ')
            else:
                uart.write(msg[i])
        if debug:
            print('\n')
    time.sleep(0.2)
    
