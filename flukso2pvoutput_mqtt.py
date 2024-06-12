import paho.mqtt.client as mqtt
import time
import requests
import json
from datetime import datetime, timedelta


# MQTT settings
MQTT_BROKER = "192.168.x.xxx"
MQTT_PORT = 1883


# PVOutput settings
PVOUTPUT_URL = "https://pvoutput.org/service/r2/addstatus.jsp"
PVOUTPUT_BATCH_URL = "https://pvoutput.org/service/r2/addbatchstatus.jsp"
PVOUTPUT_APIKEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
PVOUTPUT_SYSTEMID = "xxxxx"

BACKLOG_FILE = "/home/pi/f2pvobacklog.log"


# Sensors configuration
SENSORS = [
    # Sensor 1
    {
        "id": "sensor-id", 		# Sensor ID - Flukso Sensor id # replace the "sensor-id" section (retaining the quotation marks)
        "type": "gauge",           # Sensor type: counter or gauge (I recomend gauge for power and counter for water)
        "pvoutput_v": "v2"         # PVOutput Power Value (v1 - v12) # adjust to what suits see list below for "v" values.
    },									
    # Sensor 2							
    {									# https://pvoutput.org/help/api_specification.html
        "id": "sensor-id",						
        "type": "gauge",						# v1 - Energy Generation - kWh
        "pvoutput_v": "v4"						# v2 - Power Generation (live) - W
    },									        # v3 - Energy Consumption - kWh
    # Sensor 3							        # v4 - Power Consumption (live) - W		
    {									        # v5 - Temperature
        "id": "sensor-id",						# v6 - Voltage
        "type": "gauge",						# v7 - v12 - Extended Data 
        "pvoutput_v": "v7"						  
    },									 
    # Sensor 4							        # Counter for water/gas may require a rule pending pulse output.. 
    {									        # 1 counter is 1 pulse per _ L
        "id": "sensor-id",						# my meter is 0.5L per pulse so I have a rule "v7": "v7 / 2", # To display actual L used
        "type": "gauge",
        "pvoutput_v": "v8"
    },
    # Sensor 5
    {
        "id": "sensor-id",
        "type": "counter",
        "pvoutput_v": "v10"
    },
]

# Define the custom value adjustment rules
#
# If rules seem to be a bit backwards so	"0 (Answer) if v4 < 50 (Question and Criteria) else v4 (Answer if doesn't meet criteria)" ##Actual Rule >##  "v4": "0 if v4 < 50 else v4",
#				

CUSTOM_RULES = {
    # "v1": "v2 / 12",	#converts a live value ie. Watts to an energy value ie Wh...... but this is not needed as pvoutput alread does this.
    # "v3": "v4 / 12",
    # "v4": "v4 * 0.75",
    # "v4": "0 if v4 < 50 else v4", 	# If Rule Example
    # "v8": "v7 + 100",			#assuming v7 = 0 then v8 = 100
    # "v9": "v8 + 100", 			#v8 = 100 from above rule so v9 = 200
    # "v10": "v9 + 100", 
    # "v11": "v10 + 100", 
    # "v12": "v11 + 100", 
    # Add more rules as needed, (values update after each rule so you can use an updated value from one rule for the next rule) (the rules run from top to bottom).
}

###################################### Don't Edit Below Unless You Know What You're Doing ######################################

# Debug settings
DEBUG_SLEEP_DURATION = 0  # Default is 0  # sleep time is normally 300 seconds (5 minutes)
DEBUG_LOG = False  # True = On False = Off
DEBUG_LOG_FILE = "/home/pi/f2pvodebug.log"



# Callback function when connection to MQTT broker is established
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    for sensor in SENSORS:
        if sensor["id"]:
            sensor_topic = f"/sensor/{sensor['id']}/{sensor['type']}"
            print(f"Subscribing to topic: {sensor_topic}")
            client.subscribe(sensor_topic)

# Callback function when a message is received from MQTT broker
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received message on topic {msg.topic}: {payload}")
    
    try:
        data = json.loads(payload)
        timestamp, value, unit = data
        
        sensor_id = msg.topic.split('/')[2]
        sensor_type = msg.topic.split('/')[3]

        if sensor_type == "counter":
            reading = {"timestamp": timestamp, "value": value, "unit": unit, "sensor_id": sensor_id, "type": sensor_type}
        elif sensor_type == "gauge":
            reading = {"timestamp": timestamp, "power_value": value, "sensor_id": sensor_id}

        readings.append(reading)
    except (ValueError, TypeError) as e:
        print(f"Error processing message: {e}")
        write_debug_log(f"Error processing message: {e}")

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

# Function to adjust values based on custom rules
def adjust_values(values):
    adjusted_values = values.copy()
    for key, rule in CUSTOM_RULES.items():
        if key in adjusted_values:
            adjusted_value = evaluate_rule(rule, adjusted_values)
            if adjusted_value is not None:
                adjusted_values[key] = adjusted_value
    return adjusted_values

# Function to write debug logs
def write_debug_log(message):
    if DEBUG_LOG:
        with open(DEBUG_LOG_FILE, 'a') as log_file:
            log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Function to calculate the average power and send to PVOutput
def send_average_to_pvoutput():
    global backlog  # Declare backlog as a global variable
    
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
                if sensor['type'] == "counter":
                    initial_counter = sensor_data[0].get('value', 0)
                    final_counter = sensor_data[-1].get('value', 0)
                    usage = final_counter - initial_counter
                    if len(sensor_data) == 1:
                        usage = 0.0
                    print(f"Usage over 5 minutes for sensor {sensor_id}: {usage} L")
                    payload[sensor['pvoutput_v']] = usage
                elif sensor['type'] == "gauge":
                    total_power = sum(reading.get('power_value', 0) for reading in sensor_data if 'power_value' in reading)
                    if len(sensor_data) > 0:
                        average_power = total_power / len(sensor_data)
                        print(f"Average power over 5 minutes for sensor {sensor_id}: {average_power} W")
                        payload[sensor['pvoutput_v']] = round(average_power)
                    else:
                        print(f"No valid gauge readings for sensor {sensor_id}")

        write_debug_log(f"Initial payload: {payload}")

        adjusted_payload = adjust_values(payload)

        write_debug_log(f"Adjusted payload: {adjusted_payload}")

        # Find the keys to delete
        keys_to_delete = []
        for key in list(adjusted_payload.keys()):
            sensor_id = next((sensor['id'] for sensor in SENSORS if sensor['pvoutput_v'] == key), None)
            if adjusted_payload[key] == 0 and (sensor_id is None or len(sensor_id) != 32):
                keys_to_delete.append(key)

        # Delete the keys
        for key in keys_to_delete:
            del adjusted_payload[key]

        response = send_to_pvoutput(adjusted_payload)
        if response.status_code == 200:
            print(f"Sent data to PVOutput: {response.status_code} {response.text}")
            print(f"Payload: {adjusted_payload}")
            write_debug_log(f"Sent data to PVOutput: {response.status_code} {response.text}")
            write_debug_log(f"Payload: {adjusted_payload}")
        else:
            print(f"Failed to send data to PVOutput: {response.status_code} {response.text}")
            write_debug_log(f"Failed to send data to PVOutput: {response.status_code} {response.text}")
            backlog.append(adjusted_payload)
            save_backlog_data(backlog)
    else:
        print("No readings to send to PVOutput")

    # Attempt to send backlog data
    if backlog:
        while backlog:
            data_param = ';'.join([f"{entry['d']},{entry['t']},{entry['v1']},{entry['v2']},{entry['v3']},{entry['v4']},{entry['v5']},{entry['v6']},{entry['v7']},{entry['v8']},{entry['v9']},{entry['v10']},{entry['v11']},{entry['v12']}"
                                   for entry in backlog])
            response = send_batch_to_pvoutput(data_param)
            if response.status_code == 200:
                print(f"Backlog sent successfully: {response.status_code} {response.text}")
                write_debug_log(f"Backlog sent successfully: {response.status_code} {response.text}")
                backlog = backlog[30:]
                save_backlog_data(backlog)
            else:
                print(f"Failed to send backlog: {response.status_code} {response.text}")
                write_debug_log(f"Failed to send backlog: {response.status_code} {response.text}")

    readings.clear()

# Function to save backlog data to a file
def save_backlog_data(backlog):
    with open(BACKLOG_FILE, 'a') as f:
        f.write(json.dumps(backlog) + '\n')

# Function to load backlog data from a file
def load_backlog():
    try:
        with open(BACKLOG_FILE, 'r') as f:
            backlog = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        backlog = []
    return backlog

# Initialize MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Global variables to store readings and backlog data
readings = []
backlog = []

# Start MQTT loop
client.loop_start()

# Ensure the initial run time is at the next 5-minute interval
now = datetime.now()
initial_wait = ((5 - (now.minute % 5)) * 60 - now.second)
print(f"Initial wait time: {initial_wait} seconds")
time.sleep(initial_wait)

# Main loop to run the function every 5 minutes
while True:
    try:
        send_average_to_pvoutput()
    except Exception as e:
        print(f"Error in main loop: {e}")
        write_debug_log(f"Error in main loop: {e}")
    
    # Calculate the next run time
    now = datetime.now()
    if DEBUG_SLEEP_DURATION > 0:
        next_run_time = now + timedelta(seconds=DEBUG_SLEEP_DURATION)
    else:
        # Calculate the exact next 5-minute interval
        seconds_to_next_interval = (5 * 60 - (now.minute % 5) * 60 - now.second)
        next_run_time = now + timedelta(seconds=seconds_to_next_interval)
    
    print(f"Next run time: {next_run_time.strftime('%H:%M')}")
    
    # Sleep until the next run time
    time.sleep((next_run_time - now).total_seconds())
