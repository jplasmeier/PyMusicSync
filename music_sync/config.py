# config.py
# Configuration module for Mass Media Sync.
import json

"""
Config JSON Schema:

google_drive_secret (?)
google_drive_folder_name

usb_device_path
usb_device_sn (from IOREG)

"""

CONFIG_FILE = 'config.json'


def load_google_drive_folder_name():
    """
    Get the name of the Google Drive folder to sync with.
    :return: The name of the Google Drive folder to sync with.
    """
    config_json = load_config_json()
    return config_json['google_drive_folder_name']


def load_google_drive_test_folder_name():
    """
    Get the name of the Google Drive folder to sync with.
    :return: The name of the Google Drive folder to sync with.
    """
    config_json = load_config_json()
    return config_json['google_drive_test_folder_name']


def load_usb_device_path():
    """
    Get the name of the local path to sync with.
    :return: The name of the local path to sync with.
    """
    config_json = load_config_json()
    return config_json['usb_device_path']

def load_config_json():
    with open(CONFIG_FILE) as cfg:
        return json.load(cfg)