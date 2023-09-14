import os
import adafruit_requests as requests
import ipaddress
import ssl
import json
import wifi
import socketpool
import time
import random
import alarm
from adafruit_magtag.magtag import MagTag
from context import context

magtag = MagTag()
magtag.peripherals.neopixel_disable = False
# holder for clues to AI
clue_answers = ["left", "right", "up", "down"]

#Format text display on MagTag 
magtag.add_text(
    text_scale=1,
    text_wrap=47,
    text_maxlen=600,
    text_position=(10, 10),
    text_anchor_point=(0, 0),
)
# Define response holder
response = ""

# Set the model context
context = context

# Set a win state variable
win_state = False

# Load in the OpenAI API key
try:
    from secrets import secrets
    print("Successfully imported secrets!")
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

api_key = secrets["OPENAI_API_KEY"]
openai_api_url = "https://api.openai.com/v1/completions"

# Connect to WiFi
print("Available WiFi networks:")
for network in wifi.radio.start_scanning_networks():
    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
            network.rssi, network.channel))
wifi.radio.stop_scanning_networks()

print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
    

def get_response(prompt, answer):
    """Sends a request to OpenAI API and returns the response
    """
    # include the answer in the prompt, format like examples in context.py
    prompt = prompt + "\nWord: " + answer + "\nClue: "
    #start an HTTPS request
    https = requests.Session(pool, ssl.create_default_context())
    #Set up OpenAI API authentication
    headers = {'Authorization': f'Bearer {api_key}'}

    #Set up the model request parameters
    data = {'model': 'text-davinci-003', 'prompt': prompt, 'max_tokens': 120, 'temperature': 1.2, 'frequency_penalty': 2, 'presence_penalty': 0}
    
    # Call the OpenAI model API
    response = https.post(openai_api_url, json=data, headers=headers)
    # Set the model response as json format
    json_resp = response.json()
    try:
        # Parse json response
        response = json_resp["choices"][0]["text"]
    except Exception:
        print("Error in getting response...")
    return response

def choose_word(words):
    """This function chooses a word from the list of words to prompt the AI."""
    word = random.choice(words)
    return word

def neopixel_win_sequence():
    """Plays a fun light-up sequence when a player wins the puzzle game!"""
    for i in range(8):
        magtag.peripherals.neopixels[0] = (0, 0, 255)
        time.sleep(0.1)
        magtag.peripherals.neopixels[2] =(255,51,221)
        time.sleep(0.1)
        magtag.peripherals.neopixels[1] =(26,153,0)
        time.sleep(0.1)
        magtag.peripherals.neopixels[3] =(255,255,255)
        time.sleep(0.1)
        magtag.peripherals.neopixels.fill((0,0,0))
        i += 1

def neopixel_lose_sequence():
    """ Turns all neopixel lights red"""
    magtag.peripherals.neopixels.fill((255,0,0))


def start_new_game():
    """A function to query the player if they want to start a new game."""
    button_press = False
    magtag.set_text("Press any button to play again.")
    while not button_press:
        button_press = magtag.peripherals.any_button_pressed
    magtag.peripherals.neopixels.fill((255,255,255))
    magtag.set_text("Starting new game")
    time.sleep(4)
    magtag.peripherals.neopixels.fill((0,0,0))
    magtag.refresh()

def check_answer(answer, win_state):
    """This function compares the answer to the clue to the player's input."""
    if answer == "left": 
        if magtag.peripherals.button_a_pressed:
            win_state = True
            magtag.set_text("Correct! You win!!")
            neopixel_win_sequence()
        elif magtag.peripherals.button_b_pressed or magtag.peripherals.button_c_pressed or magtag.peripherals.button_d_pressed:
            neopixel_lose_sequence()
            time.sleep(4)
            magtag.peripherals.neopixels.fill((0,0,0))
            win_state = False
    elif answer == "right": 
        if magtag.peripherals.button_d_pressed:
            win_state = True
            magtag.set_text("Correct! You win!!")
            neopixel_win_sequence()
        elif magtag.peripherals.button_a_pressed or magtag.peripherals.button_b_pressed or magtag.peripherals.button_c_pressed:
            neopixel_lose_sequence()
            time.sleep(4)
            magtag.peripherals.neopixels.fill((0,0,0))
            win_state = False
    elif answer =="up": 
        if magtag.peripherals.button_b_pressed:
            win_state = True
            magtag.set_text("Correct! You win!!")
            neopixel_win_sequence()
        elif magtag.peripherals.button_a_pressed or magtag.peripherals.button_c_pressed or magtag.peripherals.button_d_pressed:
            neopixel_lose_sequence()
            time.sleep(4)
            magtag.peripherals.neopixels.fill((0,0,0))
    elif answer == "down" :
        if magtag.peripherals.button_c_pressed:
            win_state  = True
            magtag.set_text("Correct! You win!!")
            neopixel_win_sequence()
        elif magtag.peripherals.button_a_pressed or magtag.peripherals.button_b_pressed or magtag.peripherals.button_d_pressed:
            neopixel_lose_sequence()
            time.sleep(4)
            magtag.peripherals.neopixels.fill((0,0,0))
            win_state = False
    return win_state 
    
while True:
    try:
        win_state = False
        # pick a word to generate a clue
        answer = choose_word(clue_answers)
        # Add context and previous response to new prompt (to get a new response)
        response = get_response(context + response, answer)
        # Print the clue!
        magtag.set_text("ADA: {}".format(response))
        while not win_state: 
            win_state = check_answer(answer, win_state)
        start_new_game() 

    except (ValueError, RuntimeError) as e:
        print("Some error occurred, retrying! -", e)