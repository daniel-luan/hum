import pywinusb.hid as hid
import AudioController as AC
from time import sleep
from pathlib import Path
import json

LAST_DATA = {}
PROCESS = {}


def map_val(ival, imin, imax, omin, omax):
    """
    Map input ival ranging from imin to imax to 
    corresponding value raning from omin omax
    Args:
        ival (int): Input value.
        imin (int): Input min.
        imax (int): Input max.
        omin (int): Output Min.
        omax (int): Output Max.

    Returns:
        int: The output value.

    """
    return round((omax - omin) * (ival - imin) / (imax - imin) + omin, 2)


def get_device():
    """
    Gets the first usb hid device with the cendor_id 0x2341.
    Will raise Exception and return False if no device is pluged in. 

    Returns:
        HidDevice: The target hid device. False if no device is found.

    """
    devices = hid.HidDeviceFilter(vendor_id=0x2341).get_devices()
    if not devices:
        raise Exception("No device found!")
        return False
    return devices[0]


def data_handler(data):
    """
    Data handler callback function, called when new data is available.

    Args:
        data (list): raw hid data

    """
    global LAST_DATA

    new_data = {}
    for i in range(data[1]):
        new_data[i] = (map_val(data[i + 2], 0, 100, 0, 1), data[i + 7])

    if not LAST_DATA:
        for key in new_data.keys():
            LAST_DATA[key] = (0, 1)
    if LAST_DATA != new_data:
        for key in new_data.keys():
            if new_data[key] != LAST_DATA[key]:
                if new_data[key][0] != LAST_DATA[key][0]:
                    if key in PROCESS:
                        PROCESS[key].set_volume(new_data[key][0])
                    elif key == 0:
                        AC.set_master_volume(new_data[key][0])
                else:
                    if key in PROCESS:
                        PROCESS[key].mute(new_data[key][1])
                    elif key == 0:
                        AC.set_master_mute(not new_data[key][1])
    LAST_DATA = new_data


def print_processes(p):
    """
    Pretty print all processes for user.

    Args:
        p (list): list of processes

    """
    processes = p[:]
    processes.insert(0, ("PID", "Name", "Description"))
    pid_max_len = max([len(str(x[0])) for x in processes]) + 1
    name_max_len = max([len(str(x[1])) for x in processes]) + 1
    des_max_len = max([len(str(x[2])) for x in processes]) + 1
    max_total = sum((pid_max_len, name_max_len, des_max_len))
    print("Process List".center(max_total, "-"))
    for process in processes:
        print(str(process[0]).ljust(pid_max_len), end="")
        print(str(process[1]).rjust(name_max_len), end="")
        print(str(process[2]).rjust(des_max_len))


def print_list():
    """
    Pretty print the list of processes currently bounded.

    """
    max_len = max([len(process.process_name) for process in PROCESS.values()])
    begin = "+----+{}+".format("-" * (max_len + 2))
    print(begin)
    print("| CH | {}|".format("Name".ljust(max_len+1)))
    print(begin)
    print("| 0  | {}|".format("Master Volume".ljust(max_len+1)))
    for ch, process in PROCESS.items():
        print("| {}  | {}|".format(ch, process.process_name.ljust(max_len+1)))

    print(begin)


def get_input(p):
    """
    Ask user to select a channel for a process.
    
    Args:
        p (tuple): (process name, pid)

    Returns:
        int: The target channel. False if not selected.

    """
    i = input("\nBind to process {}({})?(y/N)".format(p[1], p[0]))
    if i and (i.lower() == "yes" or i.lower() == "y" or i == "1"):
        while True:
            i = input("Target Channel(Enter to cancel): ")
            if not i:
                return False
            if int(i) not in PROCESS:
                return int(i)
            else:
                print("Channel Taken!")

    return False


def scan():
    """
    Scans for new processes, and print them by calling print_processes().
    Then asks for user channel input by calling get_input().

    """
    global PROCESS
    PROCESS = {}
    processes = AC.get_processes()
    print_processes(processes)
    print("")
    for process in processes:
        ch = get_input(process)
        if ch:
            PROCESS[ch] = AC.AudioController(process[1])
    print_list()

def load_setting(file_name):
    """
    Load the settings from file, if file_name does not exist, then do a scan.

    Args:
        file_name (string): Name of the setting file.

    """
    if not Path(file_name).is_file():
        return scan()
    global PROCESS
    with open(file_name) as file:
        print("Loading from file \"{}\"\n".format(file_name))
        data = json.load(file)
        PROCESS = {int(k):AC.AudioController(v) for k,v in data.items()}
    print_list()


def main():
    device = get_device()
    if not device:
        return
    load_setting("settings.json")

    device.open()
    device.set_raw_data_handler(data_handler)

    while True:
        input("\n\nHit Enter to rescan for processes")
        scan()

    # while True:
    # 	print(device.is_plugged())
    # 	sleep(1)

if __name__ == '__main__':
    main()
