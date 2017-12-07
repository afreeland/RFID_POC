#! /usr/bin/env python3

import RPi.GPIO as GPIO
import serial

import webbrowser
import threading
import json
import requests

# pip install git+https://github.com/Pithikos/python-websocket-server

from websocket_server import WebsocketServer

ENABLE_PIN  = 24              # The BCM pin number corresponding to GPIO1
SERIAL_PORT = '/dev/ttyS0'

# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	server.send_message_to_all("Hey all, a new client has joined us")

# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])

def validate_rfid(code):
    # A valid code will be 12 characters long with the first char being
    # a line feed and the last char being a carriage return.
    s = code.decode("ascii")

    if (len(s) == 12) and (s[0] == "\n") and (s[11] == "\r"):
        # We matched a valid code.  Strip off the "\n" and "\r" and just
        # return the RFID code.
        return s[1:-1]
    else:
        # We didn't match a valid code, so return False.
        return False
    
k = 0

# Called when a client sends a message
def message_received(client, server, message):
    global k
    if len(message) > 200:
        message = message[:200]+'..'

    if message == 'show number':
        k = k + 1
        server.send_message_to_all( str(k) )

    print("Client(%d) said: %s" % (client['id'], message))


PORT=9001
server = WebsocketServer(PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)

threading.Thread(target=server.run_forever()).start()

def writeJSON(data):

    with open('./WebTest/data.json', 'w') as outfile:
        json.dump(data, outfile)

def main():
    # Initialize the Raspberry Pi by quashing any warnings and telling it
    # we're going to use the BCM pin numbering scheme.
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # This pin corresponds to GPIO1, which we'll use to turn the RFID
    # reader on and off with.
    GPIO.setup(ENABLE_PIN, GPIO.OUT)

    # Setting the pin to LOW will turn the reader on.  You should notice
    # the green LED light on the reader turn red if successfully enabled.

    print("Enabling RFID reader and reading from serial port: " + SERIAL_PORT)
    GPIO.output(ENABLE_PIN, GPIO.LOW)

    # Set up the serial port as per the Parallax reader's datasheet.
    ser = serial.Serial(baudrate = 2400,
                        bytesize = serial.EIGHTBITS,
                        parity   = serial.PARITY_NONE,
                        port     = SERIAL_PORT,
                        stopbits = serial.STOPBITS_ONE,
                        timeout  = 1)

    # Wrap everything in a try block to catch any exceptions.
    try:
        # Loop forever, or until CTRL-C is pressed.
        while 1:
            print("read")
            # Read in 12 bytes from the serial port.
            data = ser.read(12)
            print(data)
            # Attempt to validate the data we just read.
            code = validate_rfid(data)

            # If validate_rfid() returned a code, display it.
            if code:
                print("Read RFID code: " + code);
                userData = {}
                userData['rfid'] = code
                userData['type'] = 'user_identified'
                resp = requests.get('https://api.airtable.com/v0/appsQvYR5fOrntcrK/Users?view=Grid%20view&filterByFormula=(Tag="'+code+'")&api_key=keylGkO6A4FCxtKxS')
                if resp.status_code != 200:
                    # This means something went wrong.
                    raise ApiError('GET /tasks/ {}'.format(resp.status_code))
                userData['user'] = resp.json()
                server.send_message_to_all(json.dumps(userData))
    except:
        # If we caught an exception, then disable the reader by setting
        # the pin to HIGH, then exit.
        print("Disabling RFID reader...")
        GPIO.output(ENABLE_PIN, GPIO.HIGH)

        
if __name__ == "__main__":
    main()
