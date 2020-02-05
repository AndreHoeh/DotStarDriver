from random import randint
from adafruit_featherwing import dotstar_featherwing
from digitalio import DigitalInOut, Direction, Pull
from adafruit_seesaw.seesaw import Seesaw
from micropython import const
import time
import board
import busio


# pylint: disable=bad-whitespace
BUTTON_RIGHT = const(6)
BUTTON_DOWN = const(7)
BUTTON_LEFT = const(9)
BUTTON_UP   = const(10)
BUTTON_SEL  = const(14)
NORMAL      = const(0)
POINTLINE   = const(1)
SPEEDLINE   = const(2)
RAINBOWROAD = const(3)
# pylint: enable=bad-whitespace
button_mask = const((1 << BUTTON_RIGHT) |
                    (1 << BUTTON_DOWN) |
                    (1 << BUTTON_LEFT) |
                    (1 << BUTTON_UP) |
                    (1 << BUTTON_SEL))
numbers = {
    '0': [0x1E, 0x21, 0x1E],
    '1': [0x11, 0x3F, 0x01],
    '2': [0x13, 0x25, 0x19],
    '3': [0x21, 0x29, 0x16],
    '4': [0x38, 0x08, 0x3F],
    '5': [0x39, 0x29, 0x26],
    '6': [0x1E, 0x29, 0x06],
    '7': [0x23, 0x2C, 0x30],
    '8': [0x16, 0x29, 0x16],
    '9': [0x10, 0x29, 0x1E],
}

# TODO do with triples
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    if (pos < 0):
        return [0, 0, 0]
    if (pos > 255):
        return [0, 0, 0]
    if (pos < 85):
        return [int(pos * 3), int(255 - (pos*3)), 0]
    elif (pos < 170):
        pos -= 85
        return [int(255 - pos*3), 0, int(pos*3)]
    else:
        pos -= 170
        return [0, int(pos*3), int(255 - pos*3)]

# One pixel connected internally!
# dot = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)

i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus)
ss.pin_mode_bulk(button_mask, ss.INPUT_PULLUP)

dS = dotstar_featherwing.DotStarFeatherWing()
dS.auto_write = False
# dS.brightness = 0.2

purple = (100, 0, 100)
black = (0, 0, 0)
flash = (250, 220, 220)
turquoise = (0, 100, 50)
red = (220, 0, 0)
green = (0, 220, 0)
blueish = (0, 0, 150)

# World tiles
wall = turquoise
wallStroke = blueish
pellet = (60, 0, 0)
specialPellet = (100, 80, 0)
player = red

# Define one row of the Wolrd
# Those rows can be shifted to simulate a path
row = (wall, wall, wall, wall,
       wall, wall, wall, wallStroke,
       black, black, black, black, black,
       wallStroke, wall, wall, wall,
       wall, wall, wall, wall)

def run():
    player_x = 6
    player_y = 2
    score = 0
    steps = 0
    wallType = NORMAL
    step_delay = 0.18
    offset = 4
    coBefPl = black #Farbe, die durch Player verdeckt wurde
    rainbowVal = 0
    rainbowColor = [0, 0, 0]

    # Draw Wolrd
    for y in range(0, dS.rows):
        for x in range(0, dS.columns):
            dS[x, y] = row[x + offset]

    dS[player_x, player_y] = player
    dS.show()
    time.sleep(1)
    timePassed = time.monotonic()  # Time in seconds since power on

    while True:
        # Update some things
        steps += 1
        if steps % 25 == 0:
            score += 1
            if not wallType == RAINBOWROAD:
                wallType = POINTLINE
        if steps % 100 == 0:
            step_delay *= 0.9 # increase speed
            if not wallType == RAINBOWROAD:
                wallType = SPEEDLINE
        if wallType == RAINBOWROAD:
            rainbowVal += 5
            if rainbowVal > 220:
                rainbowVal = 0
                wallType = NORMAL
            rainbowColor = wheel(rainbowVal)

        # Remove player
        dS[player_x, player_y] = coBefPl #Farbe von vorher

        # Drive
        dS.shift_down()

        # Adjust player position
        joy_x = ss.analog_read(3)
        if joy_x < 256 and player_x > 0:
            player_x -= 1
        elif joy_x > 768 and player_x < 11:
            player_x += 1
        joy_y = ss.analog_read(2)
        if joy_y < 256 and player_y < 4:
            player_y += 1
        elif joy_y > 768 and player_y > 0:
            player_y -= 1

        # Read Button Inputs
        buttons = ss.digital_read_bulk(button_mask)
        if not buttons & (1 << BUTTON_RIGHT):
            # Does Nothing
            print("Button pressed")
        if not buttons & (1 << BUTTON_DOWN):
            print("Button pressed")
        if not buttons & (1 << BUTTON_LEFT):
            print("Button pressed")
        if not buttons & (1 << BUTTON_UP):
            print("Button pressed")
        if not buttons & (1 << BUTTON_SEL):
            print("Button pressed")

        # Player background speichern
        coBefPl = dS[player_x, player_y]

        # Place Player back into world
        dS[player_x, player_y] = player

        # Generate random track offset
        offset = min(max(0, offset + randint(-1, 1)), 9)

        # Draw a new top row
        if wallType == NORMAL:
            for x in range(0, dS.columns):
                dS[x, dS.rows -1] = row[x + offset]
        else:
            for x in range(0, dS.columns):
                if row[x + offset] == wall:
                    if wallType == POINTLINE:
                        dS[x, dS.rows -1] = wallStroke
                    elif wallType == SPEEDLINE:
                        dS[x, dS.rows -1] = green
                    elif wallType == RAINBOWROAD:
                        dS[x, dS.rows -1] = (rainbowColor[0], rainbowColor[1], rainbowColor[2])
                else:
                    dS[x, dS.rows -1] = row[x + offset]
            if not wallType == RAINBOWROAD:
                wallType = NORMAL

        # Add random pellet in top row
        if randint(1, 15) == 1:
            dS[randint(9, 11) - offset, dS.rows -1] = pellet
        if randint(1, 150) == 1:
            dS[randint(9, 11) - offset, dS.rows -1] = specialPellet

        # Check collision
        if coBefPl == wallStroke or coBefPl == wall:
            return score
        elif coBefPl == pellet:
            if wallType == RAINBOWROAD:
                score += 5
            if player_y == 4:
                score += 5
            elif player_y == 3:
                score += 3
            elif player_y < 3:
                score += 1
            dS[player_x, player_y] = flash
        elif coBefPl == specialPellet:
            score += 10
            wallType = RAINBOWROAD
            rainbowVal = 0
            step_delay *= 1.1 # decrease speed

        dS.show()
        # time.sleep(step_delay)

        # Wait until step_delay seconds have passed
        while time.monotonic() - timePassed < step_delay:
            time.sleep(0.001)
        timePassed = time.monotonic()
while True:
    result = run()
    if result > 999:
        result = 999
    scoreDigits = [] # List for score digits
    cursor = 0 # Cursor position
    print("GAME OVER")
    print(result)
    # Clear Screen
    for y in range(0, dS.rows):
        for x in range(0, dS.columns):
            dS[x, y] = black

    # generate score digit list from result
    scoreDigits.append( numbers[ (str(result))[0] ] )
    if result >= 10:
        scoreDigits.append( numbers[ (str(result))[1] ] )
    if result >= 100:
        scoreDigits.append( numbers[ (str(result))[2] ] )

    #Print score digits
    for n in range(len(scoreDigits)):
        for c in range(3):
            if ((scoreDigits[n])[c]) & 0b00000001:
                dS[c + cursor, 0] = red
            if ((scoreDigits[n])[c]) & 0b00000010:
                dS[c + cursor, 1] = red
            if ((scoreDigits[n])[c]) & 0b00000100:
                dS[c + cursor, 2] = red
            if ((scoreDigits[n])[c]) & 0b00001000:
                dS[c + cursor, 3] = red
            if ((scoreDigits[n])[c]) & 0b00010000:
                dS[c + cursor, 4] = red
            if ((scoreDigits[n])[c]) & 0b00100000:
                dS[c + cursor, 5] = red
        cursor += 4 # 3 for Number + 1 for space
    cursor = 0
    dS.show()
    time.sleep(6)
