from termcolor import colored


def device_list_has(device, device_list):
    for devlist_device in device_list:
        if device.device_id == devlist_device.device_id:
            device_list.remove(devlist_device)
            return True
    return False


def compare_device_list(current_devices, old_devices):
    if callable(getattr(current_devices, "filter", None)):
        current_devices = [obj for obj in current_devices.all()]

    if callable(getattr(old_devices, "filter", None)):
        old_devices = [obj for obj in old_devices.all()]

    device_total_change = len(current_devices) - len(old_devices)
    if device_total_change == 0:
        device_total_change = ""
    elif device_total_change > 0:
        device_total_change = "(" + colored(f"+{device_total_change}", "yellow") + ")"
    else:
        device_total_change = "(" + colored(f"{device_total_change}", "red") + ")"

    print("Previous device amount is", len(old_devices))
    if device_total_change == "":
        print(
            f"Current device amount is",
            colored(f"{len(current_devices)}", "green"),
            "too",
        )
    else:
        print("Current device amount is", len(current_devices), device_total_change)

    # Looking for missing devices
    print()
    missing_devices = []

    current_devices_copy = current_devices.copy()

    for old_device in old_devices:
        if not device_list_has(old_device, current_devices_copy):
            missing_devices.append(old_device)

    if len(missing_devices) != 0:
        print(
            colored(f"{len(missing_devices)} device(s) are missing. These are: ", "red")
        )
        for count, dev in enumerate(missing_devices):
            print()
            print(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
    else:
        print(colored("No devices are missing, hooray!", "green"))

    # Looking for new devices
    print()
    new_devices = []

    old_devices_copy = old_devices.copy()

    for new_device in current_devices:
        if not device_list_has(new_device, old_devices_copy):
            new_devices.append(new_device)

    if len(new_devices) != 0:
        print(colored(f"{len(new_devices)} device(s) are new. These are: ", "yellow"))
        for count, dev in enumerate(new_devices):
            print()
            print(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
    else:
        print(colored("No new devices found", "green"))
