from time import sleep
from random import randint
from adafruit_featherwing import dotstar_featherwing
from digitalio import DigitalInOut, Direction, Pull
from adafruit_seesaw.seesaw import Seesaw
from micropython import const
import board
import busio

# pylint: disable=bad-whitespace
BUTTON_RIGHT = const(6)
BUTTON_DOWN  = const(7)
BUTTON_LEFT  = const(9)
BUTTON_UP    = const(10)
BUTTON_SEL   = const(14)
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

i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus)
ss.pin_mode_bulk(button_mask, ss.INPUT_PULLUP)

wing = dotstar_featherwing.DotStarFeatherWing()
wing.auto_write = False
# wing.brightness = 0.2

purple = (100, 0, 100)
black = (0, 0, 0)
flash = (250, 220, 220)
turquoise = (0, 100, 50)
red = (220, 0, 0)
green = (0, 220, 0)
blueish = (0, 0, 150)

wall = turquoise
wallStroke = blueish
pellet = (60, 0, 0)
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
    pointLine = 0
    speedLine = 0
    step_delay = 0.15
    offset = 4
    coBefPl = black #Farbe, die durch Player verdeckt wurde

    # Draw Wolrd
    for y in range(0, wing.rows):
        for x in range(0, wing.columns):
            wing[x, y] = row[x + offset]

    wing[player_x, player_y] = player
    wing.show()
    sleep(1)

    while True:
        # Update some things
        steps += 1
        if steps % 25 == 0:
            score += 1
            pointLine = 1
        if steps % 100 == 0:
            step_delay *= 0.9
            speedLine = 1

        # Remove player
        wing[player_x, player_y] = coBefPl #Farbe von vorher

        # Drive
        wing.shift_down()

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
        coBefPl = wing[player_x, player_y]

        # Place Player back into world
        wing[player_x, player_y] = player

        # Generate random track offset
        offset = min(max(0, offset + randint(-1, 1)), 9)

        # Draw a new top row
        if pointLine:
            pointLine = 0
            if speedLine:
                speedLine = 0
                for x in range(0, wing.columns):
                    if row[x + offset] == wall:
                        wing[x, wing.rows -1] = green
                    else:
                        wing[x, wing.rows -1] = row[x + offset]
            else:
                for x in range(0, wing.columns):
                    if row[x + offset] == wall:
                        wing[x, wing.rows -1] = wallStroke
                    else:
                        wing[x, wing.rows -1] = row[x + offset]
        else:
            for x in range(0, wing.columns):
                wing[x, wing.rows -1] = row[x + offset]

        # Add random pellet in top row
        if randint(1, 15) == 1:
            wing[randint(9, 11) - offset, wing.rows -1] = pellet

        # Check collision
        if coBefPl == wallStroke or coBefPl == wall:
            return score
        elif coBefPl == pellet:
            if player_y == 4:
                score += 5
            elif player_y == 3:
                score += 3
            elif player_y < 3:
                score += 1
            wing[player_x, player_y] = flash

        wing.show()
        sleep(step_delay)

while True:
    result = run()
    if result > 999:
        result = 999
    scoreDigits = [] # List for score digits
    cursor = 0 # Cursor position
    print("GAME OVER")
    print(result)
    # Clear Screen
    for y in range(0, wing.rows):
        for x in range(0, wing.columns):
            wing[x, y] = black

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
                wing[c + cursor, 0] = red
            if ((scoreDigits[n])[c]) & 0b00000010:
                wing[c + cursor, 1] = red
            if ((scoreDigits[n])[c]) & 0b00000100:
                wing[c + cursor, 2] = red
            if ((scoreDigits[n])[c]) & 0b00001000:
                wing[c + cursor, 3] = red
            if ((scoreDigits[n])[c]) & 0b00010000:
                wing[c + cursor, 4] = red
            if ((scoreDigits[n])[c]) & 0b00100000:
                wing[c + cursor, 5] = red
        cursor += 4 # 3 for Number + 1 for space
    cursor = 0
    wing.show()
    sleep(6)
