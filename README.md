# FluksoToPVoutput
### This sends the flukso sensor data to pvoutput it can be uploaded from v2 to v12.

Im just learning myself so hope this works still work in progress so bare with me on the readme/files Trying to make this easy to follow with minimal knowledge like myself.

happy to help through the pvoutput community forums https://forum.pvoutput.org/

I use winscp to access the filesystem to make it easier for copy pasting etc when running headless and accessing via ssh otherwise just download and move or create and paste etc from the pi

## Requirements
1. Flukso Device
2. Pi or something that runs 24/7 that can run python script and the other dependencies
   - I reccomend to have it hooked up to a screen, mouse and keyboard to setup and google how to enable ssh so you can run it headless later.
     - I use Winscp (file manager) and Putty (terminal access) to access it from my windows pc to do 99% of the work on it. makes it easier to do everything imo especially headless

## How to Install
1. Open terminal from the desktop of the Pi or device. run the commands in the codebox in terminal 
2. Update the packages/repositries. - `sudo apt-get update`
3. Install python if not installed `python --version ` - if you dont have this installed a quick google will show you what to do.
   - FYI The official 'Bullseye' release of RPi OS contains Python 3.9.2
4. Install python addons `pip install requests` and `pip install paho-mqtt`
5. Install the MQTT Broker `sudo apt install mosquitto mosquitto-clients`

6. Create mqtt-pvoutput.py - download the `mqtt_pvoutput.py` file from here and save/move it to `/home/pi/`

7. You will have to open and edit the mqtt-pvoutput.py with your flukso Ip address, sensor id's and pvoutput details etc should be pretty self explanatory
   - Double click the file, or open it in winscp 
8. create the backlog file (this is for saving the data if it fails to send so it can try and upload it later)
   -`touch /home/pi/fluksotopvoutputbacklog.log` and then give it the correct permissions `sudo chmod 666 /home/pi/fluksotopvoutputbacklog.log`
9. Test that it works `python /home/pi/mqtt_pvoutput.py` or `python3 /home/pi/mqtt_pvoutput.py`
   - if you see mqtt data getting listed then your all good! - press ctrl + c to close


## create the service that runs on startup
1. download `mqtt_pvoutput.service` this file needs to be placed in `/etc/systemd/system/`
2. Reload systemd to Recognize the New Service - `sudo systemctl daemon-reload  `
3. Enable the Service to Start on Boot - `sudo systemctl enable mqtt_pvoutput.service`
4. Start the Service - `sudo systemctl start mqtt_pvoutput.service`
5. Check the Status of the Service - `sudo systemctl status mqtt_pvoutput.service`

## Notes
### Stop/Start/Status of the service
1. `sudo systemctl stop mqtt_pvoutput.service`
2. `sudo systemctl start mqtt_pvoutput.service`
3. `sudo systemctl status mqtt_pvoutput.service`

### troubleshooting 
if your having issues stop the service using above stop command  and then run `python /home/pi/mqtt_pvoutput.py`  to see if you can see what the error/problem is (Ctrl + C to close). 
  - After testing on another device i have had to use `python3 /home/pi/mqtt_pvoutput.py` for some reason. 
  - dont forget to start the service again or reboot the device 

### Extra information
This is definately a very alpha version with very minimal testing it may have issues. 

