import logging as log
import subprocess
import re





def log_error(text):
    print("\n"+'\033[91m'+text+'\033[0m'+"\n")

def log_success(text):
    print("\n"+"\033[92m"+text+"\033[0m" + "\n")

def methods(obj, hidden=False):
    return [[x, type(getattr(obj, x))] for x in dir(obj) if "__" not in x and not (x.startswith("_") and hidden)]

def get_options(data):
    return [{"title": item['ssid'], "text": f"{indx+1}"}
        for indx, item in enumerate(data)]


def get_choice_from_options(text, options):
    for choice in options:
        if text in [choice['title'].lower(), choice['text'].lower()]:
            return choice
    return None


def show_options(text, options):
    string = text+"\n"
    for indx, item in enumerate(options):
        string += f"{item['text']}. {item['title']}\n"
    print(string + "\n")

# Wifi Utils

def get_win_interface_info():
    interface = subprocess.check_output("netsh interface show interface")
    interface = interface.decode('utf-8')
    interface = interface.strip().split("\r\n")
    interface = [[y.strip() for y in x.split(" ") if y.strip()]
                for x in interface[2:]]
    interface = [
        {
            "admin_state": item[0],
            "state": item[1],
            "type": item[2],
            "name": item[3]
        } for item in interface
    ]
    # print(interface)
    return interface

