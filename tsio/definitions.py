import os.path
import socket
from pathlib import Path

try:
    home = str(Path.home())
except:
    home = os.path.expanduser('~')

config = configparser.ConfigParser(allow_no_value=True)

possible_folders = [os.path.join(os.path.dirname(__file__), 'conf/lanxadconfig.conf'),
                    os.path.join(os.path.dirname(__file__), "../..", 'lanxadconfig.conf'),
                    os.path.join(home, "lanxadconfig.conf"),
                    os.path.expandvars("%systemdrive%/LanxAD/lanxadconfig.conf"),
                    ]
conf_folder_to_use = None
for conf_folder in possible_folders:
    if os.path.isfile(conf_folder):
        conf_folder_to_use = conf_folder
        break
try:
    config.read(conf_folder_to_use)
except TypeError:
    raise ValueError("lanxad did not find a lanxadconfig.conf file. Please add one to an appropriate folder.")
print("LanxAD is using config file in {}".format(conf_folder_to_use))

