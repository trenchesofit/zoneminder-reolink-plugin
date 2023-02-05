"""
Project to integrate zoneminder and reolink PTZ presets
"""

import requests
import json
import logging
import configparser
import re
import fileinput
import shutil
import datetime
import sys

# noinspection PyArgumentList
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG,
                    handlers=[logging.FileHandler("zoneminder-reolink-plugin.log"), logging.StreamHandler()])

# Configuration file read
config = configparser.ConfigParser()
config.read('secrets.cfg')


def generate_code(camera):
    # Pull values from configuration file
    try:
        ip_address = config[camera]['ip']
        port = config[camera]['port']
        username = config[camera]['username']
        password = config[camera]['password']
    except Exception as config_error:
        logging.error(config_error)
        sys.exit(0)
    try:
        # Grabs the needed authentication token
        login_url = f"http://{ip_address}:{port}/cgi-bin/api.cgi?cmd=Login&token=null"
        headers = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0 (Windows NT 10.0;"
                   "Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.75 Safari/537.36",
                   "Content-Type": "application/json", "Origin": f"http://{ip_address}", "Referer":
                       f"http://{ip_address}/", "Accept-Encoding": "gzip, deflate", "Accept-Language":
                       "en-US,en;q=0.9", "Connection": "close"}
        login_json = [{"action": 0, "cmd": "Login", "param": {"User": {"password": f"{password}",
                       "userName": f"{username}"}}}]
        response = requests.post(login_url, headers=headers, json=login_json)
        login_response_json = json.loads(response.text)
        token = (login_response_json[0]['value']['Token']['name'])
        # Gets possible ptz preset positions
        preset_url = f"http://{ip_address}:{port}/cgi-bin/api.cgi?cmd=GetTime&token={token}"
        preset_json = [{"action": 1, "cmd": "GetPtzPreset", "param": {"channel": 0}}]
        response = requests.post(preset_url, headers=headers, json=preset_json)
        preset_response_json = json.loads(response.text)
        preset_data = (preset_response_json[0]['value']['PtzPreset'])
        # Iterates through preset PTZ configuration to create PHP code
        for preset in preset_data:
            if preset['enable'] == 1:
                # Removes spaces in preset names
                safe_name = preset['name'].replace(" ", "")
                # Generates PHP code to add buttons to watch.php file
                php_code = f" <form method='post'>\n <input type='submit' value='" + preset['name'] + "' name='GO" + \
                           str(preset['id']) + "'>\n <?php \n if(isset($_POST['GO" + str(preset['id']) + "']))\n { \n"\
                           "shell_exec('python3 " + safe_name + ".py'); \n echo'success'; \n } \n ?>\n" \
                                                                "<!-- End of camera configuration.-->"
                comment = f"<!-- This configuration is for reolink integration for camera " \
                          f"{preset['name']} on preset {preset}-->"
                # Generates Python code to create action files
                python_code = f'import requests\nimport json\nusername = "{username}"\npassword = "{password}"\n' \
                              f'burp0_url = "http://{ip_address}:{port}/cgi-bin/api.cgi?cmd=Login&token=' \
                              'null"\nburp0_headers = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest",' \
                              '"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, ' \
                              'like Gecko) Chrome/109.0.5414.75 Safari/537.36","Content-Type": "application/json", ' \
                              f'"Origin": "http://{ip_address}","Referer": "http://{ip_address}/", "Accept-Encoding": '\
                              '"gzip, deflate","Accept-Language": "en-US,en;q=0.9", "Connection": "close"}\n' \
                              'burp0_json = [{"action": 0, "cmd": "Login", "param": {"User": {"password": ""' \
                              '+password+"", "userName": ""+username+""}}}]\nresponse = requests.post(burp0_url, ' \
                              'headers=burp0_headers, json=burp0_json)\nresponseJson = json.loads(response.text)\n' \
                              'token = (responseJson[0]["value"]["Token"]["name"])\n' \
                              f'burp0_url = "http://{ip_address}:{port}/cgi-bin/api.cgi?cmd=GetTime&token="+token \n' \
                              'burp0_headers = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest", \n ' \
                              '"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
                              '(KHTML, like Gecko) Chrome/109.0.5414.75 Safari/537.36", \n "Content-Type": ' \
                              f'"application/json", "Origin": "http://{ip_address}", \n "Referer": "http://' \
                              f'{ip_address}/", "Accept-Encoding": "gzip, deflate", \n "Accept-Language": ' \
                              '"en-US,en;q=0.9", "Connection": "close"}\nburp0_json = [{"cmd": "PtzCtrl", "param": ' \
                              '{"channel": 0, "op": "ToPos", "id": ' + str(preset['id']) + ', "speed": 32}}] \n' \
                              'response = requests.post (burp0_url, headers=burp0_headers, json=burp0_json)'

                code_write(php_code, comment, python_code, safe_name)
        logging.info("Success! Camera presets should now be visible on the camera stream within Zoneminder.")
    except Exception as error:
        logging.error(error)


# Backup watch file before altering, save with date and time
def backup_watch():
    logging.info("Backing up the target watch.php file.")
    try:
        target_file = "/usr/share/zoneminder/www/skins/classic/views/watch.php"
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = f"/usr/share/zoneminder/www/skins/classic/views/watch.{now}.php.bak"
        shutil.copy(target_file, backup_file)
        logging.info("Backup successful")
    except IOError as e:
        logging.error(e)


# Check watch.php for previous configurations pushed to file
def code_check():
    try:
        for i, line in enumerate(open('/usr/share/zoneminder/www/skins/classic/views/watch.php')):
            for match in re.finditer("This configuration is for reolink integration for camera", line):
                logging.info(f"Previous configuration detected on line {i+1}: {match.group()}")
                return True
    except IOError as e:
        logging.error(e)


# Remove previous config / leaves last comment
def remove_previous_config():
    beginning_comment = "<!-- This configuration is for reolink"
    ending_comment = "<!-- End of camera configuration.-->"
    delete_line = False
    logging.info(f"Removing previous configuration.")
    try:
        for line in fileinput.input('/usr/share/zoneminder/www/skins/classic/views/watch.php', inplace=True):
            if beginning_comment in line:
                delete_line = True
            elif ending_comment in line:
                delete_line = False
                print(line, end='')
            elif not delete_line:
                print(line, end='')
    except IOError as e:
        logging.error(e)


# Writes code to the watch.php page and creates the needed python file action
def code_write(php_code, comment, python_code, safe_name):
    if php_code:
        try:
            with open('/usr/share/zoneminder/www/skins/classic/views/watch.php', "r+") as watch_ui:
                file_data = watch_ui.read()
                text_pattern = re.compile(re.escape("fa-exclamation-circle\"></i></button>"), flags=0)
                file_contents = text_pattern.sub(f"fa-exclamation-circle\"></i></button>\n{comment}\n{php_code}",
                                                 file_data)
                watch_ui.seek(0)
                watch_ui.truncate()
                watch_ui.write(file_contents)
        except IOError as e:
            logging.error(f"Error writing PHP code. {e}")
    if python_code:
        try:
            with open('/usr/share/zoneminder/www/'+safe_name+'.py', 'w') as python_file:
                python_file.write(python_code)
                python_file.close()
        except IOError as e:
            logging.error(f"Error writing Python code. {e}")


def main():
    boolean_response = code_check()
    backup_watch()
    if boolean_response is None:
        for camera in config.sections():
            generate_code(camera)
    else:
        remove_previous_config()
        for camera in config.sections():
            generate_code(camera)
    return 0


if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
