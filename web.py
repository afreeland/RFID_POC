import json
import webbrowser
import threading
import json

# pip install git+https://github.com/Pithikos/python-websocket-server

from websocket_server import WebsocketServer


# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	server.send_message_to_all("Hey all, a new client has joined us")
	userData = {}
	userData['rfid'] = '56'
	userData['type'] = 'user_identified'
	server.send_message_to_all(json.dumps(userData))


# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])


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

