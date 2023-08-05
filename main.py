import os
import adafruit_requests as requests
import ipaddress
import ssl
import json
import wifi
import socketpool
import time
import alarm
from adafruit_magtag.magtag import MagTag
 
magtag = MagTag()

#Format  text 
magtag.add_text(
    text_scale=1,
    text_wrap=47,
    text_maxlen=600,
    text_position=(10, 10),
    text_anchor_point=(0, 0),
)
#define response holder
response = ""

try:
    from secrets import secrets
    print("Sucessfully imported secrets!")
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

def get_response(prompt):
    """
    Returns a request to OpenAI API and returns the response
    """
    https = requests.Session(pool, ssl.create_default_context())
    with open('./requestbody.json') as f:
        data = json.load(f)

    headers = {'Authorization': f'Bearer {api_key}'}
    
    data = {'model': 'text-davinci-002', 'prompt': prompt, 'max_tokens': 120, 'temperature': 0.8, 'top_p': 1, 'frequency_penalty': 2, 'presence_penalty': 0}

    response = https.post(openai_api_url, json=data, headers=headers)
    json_resp = response.json()
    try:
        #parse json response
        response = json_resp["choices"][0]["text"]
            
    except Exception:
        print("error in getting response")

    return response

while True:
    try:
        # Print today's fun fact!
        prompt = "Today you share a new uplifting or funny fact that is different than your other previous facts."
        #Need to add response to new prompt to get a new response
        response = get_response(prompt + response)
        magtag.set_text("ADA: \n{}".format(response))
        magtag.refresh()

        # Put the board to sleep for 24 hrs 
        time.sleep(2)
        print("Sleeping")
        # TESTING PURPOSES ONLY TO BE REMOVED ------------------------------------------------------------------
        PAUSE = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 60) #new fact every min, 
        
        # BRING BACK THE FOLLOWING LINE ------------------------------------------------------------------
        #PAUSE = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 60 * 60 * 24)
        alarm.exit_and_deep_sleep_until_alarms(PAUSE)

    except (ValueError, RuntimeError) as e:
        print("Some error occured, retrying! -", e)