"""
This is a work in progress!!!

This lets a circuitpython device play and skip tracks on an ipod using the Apple Accessory Protocol.
The code is pretty messy but it does (mostly) work.

KNOWN ISSUES:
    For some reason, play/pause only plays and only works once.

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

def checksum(msg):
    checksum = 0x00
    for k in range(2, len(msg)):
        checksum += msg[k]
        
    return 0x100 - (checksum & 0xFF)

# builds the msg that we want to send to the ipod
def send_to_pod(mode, cmd, param, paramLen):
    uart = busio.UART(board.TX, rx=None, bits=8, parity=None, stop=1, baudrate=19200) #8N1
    # SIZE= 1 for mode + 2 for command + N for param
    msg[2]=1+2+paramLen
    msg[3]=mode
    msg[4]=cmd[0]
    msg[5]=cmd[1]

    # for now, length will always be zero.  if we entered mode 4 this might change...
    if paramLen == 0:
        msg[6] = 0
    else:
        for j in range(0, paramLen):
            msg[6+j] = param[j]

    # load up the checksum
    msg[6+paramLen]=checksum(msg)

    # send the message to the ipod!
    for j in range(0, (7 + paramLen)):
        if debug:
            print(bytes([msg[j]]))
        else:
            uart.write(bytes([msg[j]]))
    if debug:
        print("\n")

switchMode2 = (1,2)
buttonRelease = (0,0)
playPause = (0,1)
volUp = (0,2)
volDown = (0,4)
skipForward = (0,8)

msg = [0] * 10 #msg format [Sync, Start, Len, Mode, Command, Param, Checksum]
msg[0] = 0xFF # Sync Byte. Always include
msg[1] = 0x55 # Packet start byte. Always include

params = []

start = time.time()
send_to_pod(0, switchMode2, params, 0)
end = time.time()
print(end-start)
#msg.append(0x03) # Packet Payload Length
#msg.append(0x00) # Lingo ID for General Lingo
#msg.append(0x01) # First command byte
#msg.append(0x02) # Second command byte
#msg.append(bytes([checksum(msg)])) # Checksum

time_ran = 0
while True:
    if playButton.value:
        # sends the play command
        send_to_pod(0, playPause, params, 0)
        # The release button command
        send_to_pod(0, buttonRelease, params, 0)
    if skipButton.value:
        # sends the skip button command
        send_to_pod(0, skipForward, params, 0)
        # The release button command
        send_to_pod(0, buttonRelease, params, 0)
    time.sleep(0.2)
    
