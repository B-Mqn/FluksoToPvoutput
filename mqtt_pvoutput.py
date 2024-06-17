# V1
#	This is design Purely to send Flukso data to Pvoutput using MQTT.


# 	Mqtt_pvoutput Created by Bman - https://github.com/B-Mqn/FluksoToPVoutput
# 	happy for anyone to edit it but please dont remove my credit of creating it.

#	 head over to https://forum.pvoutput.org to discuss it.


#	 I hope this is easy enough to understand for those not farmiliar with coding. 
#	for those that dont understand coding  to 'uncomment' the rules remove the # at the very start of the line. a comment gets ignored by the code so you can have the code there and uncomment for the script to see it


# 		Last but not least I dont really know much about coding at all so yes its messy. 
#		also this is still very untested and in alpha stage i only use one power sensor so its only tested with one sensor but i have hopefully designed it to use all flukso's 5 available ports.
#		This might not work for water and gas meters i do use mine with water too but thats stage 2. just getting power going is my first aim


import paho.mqtt.client as mqtt
import time
import requests
import json
from datetime import datetime

# MQTT settings
MQTT_BROKER = "192.168.xxx.xxx"	# This is your flukso local lan ip address you can log into your router or use a network scanning app like fing (on android) to find it
MQTT_PORT = 1883			# Don't change this

#Place your sensor Ids here and assign the power value (v1 to v12) penind the power value you want the sensor to correspond with -  https://pvoutput.org/help/api_specification.html

SENSORS = [
    {"id": "sensor_1_id", "pvoutput_v": "v2"},	  # Replace "sensor_1_id" with your actual sensor number (just grab it from your pvoutput settings if you had it in there)
    {"id": "sensor_2_id", "pvoutput_v": "v4"},    # Dont forget to change the v number (always keep it as a lower case v)
    {"id": "sensor_3_id", "pvoutput_v": "v7"},
    {"id": "sensor_4_id", "pvoutput_v": "v8"},
    {"id": "sensor_5_id", "pvoutput_v": "v12"},
]

# PVOutput settings	
PVOUTPUT_URL = "https://pvoutput.org/service/r2/addstatus.jsp"				# Don't change this
PVOUTPUT_BATCH_URL = "https://pvoutput.org/service/r2/addbatchstatus.jsp"		# Don't change this
PVOUTPUT_APIKEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"				# Place your 40 digit PVoutput API key in here
PVOUTPUT_SYSTEMID = "xxxxx"									# Place your 5 digit System Id key in here 

# File to store backlog data
BACKLOG_FILE = "/home/pi/fluksotopvoutputbacklog.log"					#this the location and name of the backlog file if the data isnt sent

# Define the custom value adjustment rules
CUSTOM_RULES = {
#    "v1": "v2 / 12", # uncomment this line to create cumulative data from the live 5 minute averaged data for generation (these might not be needed after reading the pvoutput documentation )
#    "v3": "v4 / 12", # uncomment this line to create cumulative data from the live 5 minute averaged data for consumption (these might not be needed after reading the pvoutput documentation )

#    "v4": "v4 * 6.421725",		# adjusting the power reading to factor in voltage and consumption clamp differences
#    "v8": "v7 + 100",         #random test
    # Add more rules as needed
}



##################################### DONT EDIT BELOW THIS LINE ##################################################

# Callback function when connection to MQTT broker is established
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    for sensor in SENSORS:
        if sensor["id"]:
            sensor_topic = f"/sensor/{sensor['id']}/gauge"
            print(f"Subscribing to topic: {sensor_topic}")
            client.subscribe(sensor_topic)

# Callback function when a message is received from MQTT broker
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received message on topic {msg.topic}: {payload}")
    
    # Extract the power value (assume it's the second value in the list)
    try:
        power_data = json.loads(payload)
        timestamp, power_value, unit = power_data
        
        # Store the power value if it's in Watts
        if unit == "W":
            sensor_id = msg.topic.split('/')[2]
            reading = {"timestamp": timestamp, "power_value": power_value, "sensor_id": sensor_id}
            readings.append(reading)
    except (ValueError, TypeError) as e:
        print(f"Error processing message: {e}")

# Function to send data to PVOutput
def send_to_pvoutput(payload):
    headers = {
        'X-Pvoutput-Apikey': PVOUTPUT_APIKEY,
        'X-Pvoutput-SystemId': PVOUTPUT_SYSTEMID
    }
    response = requests.post(PVOUTPUT_URL, data=payload, headers=headers)
    return response

# Function to send batch data to PVOutput
def send_batch_to_pvoutput(data_param):
    headers = {
        'X-Pvoutput-Apikey': PVOUTPUT_APIKEY,
        'X-Pvoutput-SystemId': PVOUTPUT_SYSTEMID
    }
    response = requests.post(PVOUTPUT_BATCH_URL, data={"data": data_param}, headers=headers)
    return response

# Define the custom value adjustment rules
def evaluate_rule(rule, values):
    try:
        return eval(rule, {}, values)
    except (NameError, SyntaxError):
        return None

def adjust_values(values):
    adjusted_values = values.copy()
    for key, rule in CUSTOM_RULES.items():
        if key in values:
            adjusted_values[key] = evaluate_rule(rule, values)
    return adjusted_values

# Function to calculate the average power and send to PVOutput
def send_average_to_pvoutput():
    global backlog  # Declare backlog as a global variable
    
    # Always reload the backlog before sending
    backlog = load_backlog()
    
    if readings:
        sensor_readings = {}
        
        # Organize readings by sensor
        for reading in readings:
            sensor_id = reading['sensor_id']
            if sensor_id not in sensor_readings:
                sensor_readings[sensor_id] = []
            sensor_readings[sensor_id].append(reading)
        
        # Prepare the payload with averaged sensor data
        payload = {
            'd': datetime.now().strftime("%Y%m%d"),
            't': datetime.now().strftime("%H:%M"),
            'v1': 0, 'v2': 0, 'v3': 0, 'v4': 0, 'v5': 0,
            'v6': 0, 'v7': 0, 'v8': 0, 'v9': 0, 'v10': 0,
            'v11': 0, 'v12': 0
        }

        for sensor in SENSORS:
            sensor_id = sensor['id']
            if sensor_id and sensor_id in sensor_readings:
                sensor_data = sensor_readings[sensor_id]
                # Calculate average power over 5 minutes
                total_power = sum(reading['power_value'] for reading in sensor_data)
                average_power = total_power / len(sensor_data)
                print(f"Average power over 5 minutes for sensor {sensor_id}: {average_power} W")

                # Set the values from the sensor average power
                payload[sensor['pvoutput_v']] = round(average_power)

        # Apply the rules after setting all sensor values
        adjusted_payload = adjust_values(payload)

        print(f"Adjusted payload: {adjusted_payload}")

        # Ensure all original sensor data is sent regardless of value, remove 0 values if sensor ID is less than 32 characters
        for key in list(adjusted_payload.keys()):
            sensor_id = next((sensor['id'] for sensor in SENSORS if sensor['pvoutput_v'] == key), None)
            if adjusted_payload[key] == 0 and (sensor_id is None or len(sensor_id) != 32):
                del adjusted_payload[key]

        print(f"Final payload after removing 0 values: {adjusted_payload}")
        
        # Send data to PVOutput
        response = send_to_pvoutput(adjusted_payload)
        
        if response.status_code == 200:
            print(f"Sent data to PVOutput: {response.status_code} {response.text}")
            print(f"Payload: {adjusted_payload}")
            # Update last successful send time
            last_success = datetime.now().timestamp()
        else:
            print(f"Failed to send data to PVOutput: {response.status_code} {response.text}")
            # Save data to backlog
            backlog.append(adjusted_payload)
            save_backlog_data(backlog)
        
        # Clear the readings list after processing
        readings.clear()

    # Try sending backlog data
    if backlog:
        backlog_data = backlog[:30]  # Send up to 30 entries at once
        
        data_param = ";".join([",".join(str(v) for v in [
            entry.get('d', ''),
            entry.get('t', ''),
            entry.get('v1', ''),
            entry.get('v2', ''),
            entry.get('v3', ''),
            entry.get('v4', ''),
            entry.get('v5', ''),
            entry.get('v6', ''),
            entry.get('v7', ''),
            entry.get('v8', ''),
            entry.get('v9', ''),
            entry.get('v10', ''),
            entry.get('v11', ''),
            entry.get('v12', '')
        ]) for entry in backlog_data])
        
        response = send_batch_to_pvoutput(data_param)
        
        if response.status_code == 200:
            print(f"Successfully sent backlog data: {response.status_code} {response.text}")
            # Remove the sent entries from the backlog
            backlog = backlog[30:]
            # Save the updated backlog to the file
            save_backlog_data(backlog)
        else:
            print(f"Failed to send backlog data: {response.status_code} {response.text}")

# Save backlog data to file
def save_backlog_data(data):
    with open(BACKLOG_FILE, 'w') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')

# Load backlog data from file
def load_backlog():
    try:
        with open(BACKLOG_FILE, 'r') as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        return []

# Load last successful send time
def load_last_success():
    try:
        with open(BACKLOG_FILE, 'r') as f:
            first_line = f.readline()
            return json.loads(first_line)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save last successful send time
def save_last_success(last_success):
    # Read existing backlog
    backlog = load_backlog()
    # Write last success as the first line, followed by backlog
    with open(BACKLOG_FILE, 'w') as f:
        f.write(json.dumps(last_success) + '\n')
        for entry in backlog:
            f.write(json.dumps(entry) + '\n')

# Initialize readings and backlog lists
readings = []
backlog = load_backlog()
last_success = load_last_success()

# Create MQTT client instance
client = mqtt.Client()

# Set callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start a loop to send data every 300 seconds
while True:
    client.loop_start()
    time.sleep(300)  # Wait for 300 seconds (5 minutes)
    client.loop_stop()
    send_average_to_pvoutput()
