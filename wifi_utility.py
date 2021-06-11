import os
import re
import subprocess
import platform as ptf

from common import get_win_config
from getpass_astk import getpass as inputpass

from utils import (get_choice_from_options,
                   get_options, log_error, log_success,
                   show_options
                   )


# get wifi networks


class WifiUtility:
    _cmds = {
        "linux": {
            "wifi_info": ["nmcli", "dev", "wifi", "list", "--rescan", "yes"],
            "delete_profile": lambda profile: ['nmcli', 'connection', 'delete', f'{profile}'],
            "add_profile": lambda profile, passwd: ['nmcli', 'dev', 'wifi', 'connect', f'{profile}', 'password', f'{passwd}'],
            "connect": lambda profile: ["nmcli", "con", "up", f"{profile}"]
        },
        "windows": {
            "wifi_info": "netsh wlan show networks mode=bssid",
            "delete_profile": lambda profile: ['netsh',"wlan", 'delete', 'profile', f"name={profile}"],
            "add_profile": lambda profile, passwd: ['netsh', 'wlan', 'add', 'profile', f'filename={profile}.xml', 'interface=Wi-Fi'],
            "connect": lambda profile: ["netsh", "wlan", "connect", f'name={profile}', f'ssid={profile}',  'interface=Wi-Fi']
        }
    }

    def __init__(self):
        self.ptf = ptf.system().lower()
        self.is_linux = self.ptf == "linux"
        self.is_windows = self.ptf == "windows"

    @staticmethod
    def get_linux_network_info(data, top=-1):

        networks = data.decode("utf-8").strip()
        networks = networks.replace(" SSID ", " NAME ")

        indx_inuse = networks.find("IN-USE")
        indx_bssid = networks.find("BSSID")
        indx_name = networks.find("NAME")
        indx_mode = networks.find("MODE")
        indx_chan = networks.find("CHAN")
        indx_rate = networks.find("RATE")
        indx_signal = networks.find("SIGNAL")
        indx_bars = networks.find("BARS")
        indx_security = networks.find("SECURITY")
        indx_last = networks.find('\n')

        slices = [[indx_inuse, indx_bssid], [indx_bssid, indx_name],
                  [indx_name, indx_mode], [indx_mode, indx_chan],
                  [indx_chan, indx_rate], [indx_rate, indx_signal],
                  [indx_signal, indx_bars], [indx_bars, indx_security],
                  [indx_security, indx_last]]

        networks = [item for item in networks.split("\n")]
        networks = [[network[item[0]:item[1]].strip() for item in slices]
                    for network in networks]
        networks = sorted([
                {
                    "ssid": item[2],
                    "bssid": item[1],
                    "signal": int(item[6])
                } for item in networks[1:]], key=lambda item: item['signal'], reverse=True)
        networks = {
            "active": len(networks),
            "networks": networks[:top] if top > 1 else networks
        }
        return networks

    @staticmethod
    def get_win_network_info(data, top=-1):
        networks = data.decode('utf-8')
        networks = networks.strip().split("\r\n\r\n")
        num_networks = re.search(r"\d", networks[0]).group()
        networks = [x.strip().split("\r\n") for x in networks[1:]]
        networks = [[[z.strip() for z in y.strip().split(":")]
                    for y in x] for x in networks]
        networks = sorted([{
                "ssid": network[0][1],
                "type": network[1][1],
                "authmode": network[2][1],
                "encryption": network[3][1],
                "signal": int(network[5][1].replace('%', ''))
            } for network in networks], key= lambda item: item['signal'], reverse=True)
        network_info = {
            "active": int(num_networks),
            "networks":  networks[:top] if top > 1 else networks
        }
        return network_info

    def get_cmd(self, cname, **kwargs):
        if kwargs:
            return self._cmds[self.ptf][cname](**kwargs)
        return self._cmds[self.ptf][cname]

    def get_wifi_info(self):
        try:
            cmd = self.get_cmd('wifi_info')
            networks = subprocess.check_output(cmd)
            if self.is_windows:
                networks = self.get_win_network_info(networks, top=3)
            if self.is_linux:
                networks = self.get_linux_network_info(networks, top=3)
                if networks.get('active') == 0:
                    return {}
            return networks
        except Exception as e:
            # print(e)
            # log_error(e.output.decode("utf-8"))
            return {}

    def delete_profile(self, profile):
        cmd = self.get_cmd('delete_profile', profile=profile)
        try:
            fh = open(os.devnull, 'w')
            output = subprocess.check_output(cmd, stderr=fh)
            fh.close()
            return True
        except subprocess.CalledProcessError as e:
            # print("OUTPUT == ", e.output)
            
            return False

    def add_profile(self, ssid, passwd):
        command = self.get_cmd('add_profile', profile=ssid, passwd=passwd)
        if self.is_windows:
            config = get_win_config(ssid, passwd)
            filename = f"{ssid}.xml"
            with open(filename, 'w+') as file:
                file.write(config)

        success = True
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            print(e.output.decode('utf-8'))
            success = False
        if self.is_windows:
            os.remove(filename)

        return success

    def connect(self, ssid, passwd):
        # if self.is_windows:
        self.delete_profile(ssid)

        self.add_profile(ssid, passwd)
        cmd = self.get_cmd('connect', profile=ssid)
        try:
            output = subprocess.check_output(cmd)
            print("OUTPUT ==", output)
            return True
        except subprocess.CalledProcessError as e:
            log_error(e.output.decode('utf-8'))
            return False

    def start_utility(self):
        info = self.get_wifi_info()
        if not info:
            log_error('No Wifi Networks available at this moment. Turn On wifi if it is turned Off')
            return
        options = get_options(info['networks'])
        text = f"There {'is' if info['active']==1 else 'are'} {info['active']} network{'s' if info['active'] != 1 else ''} available and you're viewing the top {len(options)}:\n"
        show_options(text, options)
        show_prompt = False
        while True:
            if show_prompt:
                info = self.get_wifi_info()
                if not info:
                    log_error("No Wifi Networks available at this moment")
                    return
                options = get_options(info['networks'])
                text = f"There {'is' if info['active']==1 else 'are'} {info['active']} network{'s' if info['active'] != 1 else ''} available and you're viewing the top {len(options)}:\n"
                show_options(text, options)
            message = input("Your Choice? ")
            choice = get_choice_from_options(message, options)
            if not choice:
                log_error("You have selected an invalid option")
                show_prompt = True
                continue
            # get password for ssid
            passwd = inputpass(f"\nEnter password for '{choice['title']}': ")
            connection = self.connect(choice['title'], passwd)
            if connection:
                log_success("Connection was successful!")
                break
            log_error("Connection Failed due to Incorrect password!")
            break


# Ask to select wifi network
wifi = WifiUtility()

wifi.start_utility()
# wifi.get_wifi_info()