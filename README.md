# FluksoToPVoutput V2 *** NEW VERSION *** 
## V3 in testing in the (Patch 1 Branch) -  multi rules for the same value fix
  - Fixed rules and allowed more options (still no multi rules for the same value)
  - aligned with 5 min hourly intervals
  - added gauge and counter sensor types so water/gas should work aswell now
  - and lots of bugfixes
## (Old version still available in "V1" Branch if this causes you problems)
### This sends the flukso sensor data to pvoutput it can be uploaded from v1 to v12.

Im just learning myself so hope this works still work in progress so bare with me on the readme/files Trying to make this easy to follow with minimal knowledge like myself.

Happy to help through the pvoutput community forums [https://forum.pvoutput.org/](https://forum.pvoutput.org/t/flukso-to-pvoutput-bypassing-the-flukso-server-script-discussion/7405/)

I use winscp to access the filesystem to make it easier for copy pasting etc when running headless and accessing via ssh otherwise just download and move or create and paste etc from the pi.

## Requirements
1. Flukso Device
2. Pi or something that runs 24/7 that can run python script and the other dependencies
   - I reccomend to have it hooked up to a screen, mouse and keyboard to setup and google how to enable ssh so you can run it headless later.
     - I use Winscp (file manager) and Putty (terminal access) to access it from my windows pc to do 99% of the work on it. makes it easier to do everything imo especially headless.

## How to Install
1. Open terminal from the desktop of the Pi or device. run the commands in the codebox in terminal.
2. Update the packages/repositries. - `sudo apt-get update`
3. Install python if not installed `python --version ` - if you dont have this installed a quick google will show you what to do.
   - FYI The official 'Bullseye' release of RPi OS contains Python 3.9.2
4. Install python addons `pip install requests` and `pip install paho-mqtt`
5. Install the MQTT Broker `sudo apt install mosquitto mosquitto-clients`

6. Create flukso2pvoutput_mqtt.py - download the `flukso2pvoutput_mqtt.py` file from here and save/move it to `/home/pi/`

7. You will have to open and edit the flukso2pvoutput_mqtt.py with your flukso Ip address, sensor id's and pvoutput details etc should be pretty self explanatory.
   - Double click the file, or open it in winscp 
8. create the backlog file (this is for saving the data if it fails to send so it can try and upload it later).
   -`touch /home/pi/f2pvobacklog.log` and then give it the correct permissions `sudo chmod 666 /home/pi/f2pvobacklog.log`
9. Repeat for the debug log (this can be turned on using the true flag in flukso2pvoutput_mqtt.py. It will show errors and also show initial, adjusted and posted values so you can see how the rules are working)
   -`touch /home/pi/f2pvodebug.log` and then give it the correct permissions `sudo chmod 666 /home/pi/f2pvodebug.log`
11. Test that it works `python3 /home/pi/flukso2pvoutput_mqtt.py`
   - if you see mqtt data getting listed then your all good! - press ctrl + c to close.


## create the service that runs on startup
1. download `flukso2pvoutput_mqtt.service` this file needs to be placed in `/etc/systemd/system/`
2. Reload systemd to Recognize the New Service - `sudo systemctl daemon-reload  `
3. Enable the Service to Start on Boot - `sudo systemctl enable flukso2pvoutput_mqtt.service`
4. Start the Service - `sudo systemctl start flukso2pvoutput_mqtt.service`
5. Check the Status of the Service - `sudo systemctl status flukso2pvoutput_mqtt.service`

## Notes
### Stop/Start/Status of the service
1. `sudo systemctl stop flukso2pvoutput_mqtt.service`
2. `sudo systemctl start flukso2pvoutput_mqtt.service`
3. `sudo systemctl status flukso2pvoutput_mqtt.service`

### troubleshooting 
if your having issues stop the service using above stop command  and then run `python3 /home/pi/flukso2pvoutput_mqtt.py`  to see if you can see what the error/problem is (Ctrl + C to close). 
  - This will show live mqtt data and other 5 min interval data - dont forget to start the service again or reboot the device. 
Debugging
  - Enable the debug flag in the `flukso2pvoutput_mqtt.py` file - `DEBUG_LOG = True`  # True = On False = Off
  - run the python script like above after stopping the service. and run another terminal with `tail -f /home/pi/f2pvodebug.log` to see real time debug logs (these are added every 5 minutes)
  - DONT FORGET TO TURN THIS OFF WHEN FINISHED DEBUGGING (otherwise it will constantly be writing pointless data)

### Extra information
This is definately a very alpha version with very minimal testing it may have issues. 

