# Zoneminder-Reolink-Plugin

A python script that will create clickable buttons to navigate to the ReoLink PTZ presets within the Zoneminder UI.
### Setup
To begin, create or move the configuration file named "secrets.cfg" in root of your Zoneminder installation. 
(/usr/share/zoneminder/www/) Replace the values with your ReoLink IP, port, username, and password.
```buildoutcfg
[camera1]
ip=10.0.10.103
port=80
username=admin
password=
[camera2]
ip=10.0.10.104
port=80
username=testusername
password=testpassword
```
Next, run the "zoneminder-reolink-plugin.py". No arguments are required. Root may be required depending on how you have
Zoneminder installed.
```bash
trenchesofit@zoneminder:/usr/share/zoneminder/www$ sudo python3 zoneminder-reolink-plugin.py
2023-02-05 11:43:35,721 - root - INFO - Previous configuration detected on line 71: This configuration is for reolink integration for camera
2023-02-05 11:43:35,722 - root - INFO - Backing up the target watch.php file.
2023-02-05 11:43:35,723 - root - INFO - Backup successful
2023-02-05 11:43:35,723 - root - INFO - Removing previous configuration.
2023-02-05 11:43:35,730 - urllib3.connectionpool - DEBUG - Starting new HTTP connection (1): 10.0.10.103:80
2023-02-05 11:43:35,745 - urllib3.connectionpool - DEBUG - http://10.0.10.103:80 "POST /cgi-bin/api.cgi?cmd=Login&token=null HTTP/1.1" 200 None
2023-02-05 11:43:35,749 - urllib3.connectionpool - DEBUG - Starting new HTTP connection (1): 10.0.10.103:80
2023-02-05 11:43:35,821 - urllib3.connectionpool - DEBUG - http://10.0.10.103:80 "POST /cgi-bin/api.cgi?cmd=GetTime&token=b4c1965a54516bf HTTP/1.1" 200 None
2023-02-05 11:43:35,845 - root - INFO - Success! Camera presets should now be visible on the camera stream within Zoneminder.
```
If configuration changes occur on your cameras, just re-run the "zoneminder-reolink-plugin.py" script.
