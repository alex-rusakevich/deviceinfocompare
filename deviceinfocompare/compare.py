from termcolor import colored


def device_list_has(device, device_list):
    for devlist_device in device_list:
        if device.device_id == devlist_device.device_id:
            device_list.remove(devlist_device)
            return True
    return False


def state_changed(device, old_device_list):
    for devlist_device in old_device_list:
        if device.device_id == devlist_device.device_id:
            if device.device_status != devlist_device.device_status:
                return {
                    "from": devlist_device.device_status,
                    "to": device.device_status,
                }
            else:
                return "no_changes"
    return "not_found"


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
            colored("[+]", "green"),
            "Current device amount is",
            colored(f"{len(current_devices)}", "green"),
            "too",
        )
    elif "+" in device_total_change:
        print(
            colored("[?]", "yellow"),
            "Current device amount is",
            len(current_devices),
            device_total_change,
        )
    else:
        print(
            colored("[-]", "red"),
            "Current device amount is",
            len(current_devices),
            device_total_change,
        )
    print()

    # Looking for missing devices
    missing_devices = []

    current_devices_copy = current_devices.copy()

    for old_device in old_devices:
        if not device_list_has(old_device, current_devices_copy):
            missing_devices.append(old_device)

    if len(missing_devices) != 0:
        print(
            colored(
                f"[-] {len(missing_devices)} device(s) are missing. These are: ", "red"
            )
        )
        for count, dev in enumerate(missing_devices):
            print(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
            print()
    else:
        print(colored("[+] No devices are missing, hooray!", "green"))

    # Looking for new devices
    new_devices = []

    old_devices_copy = old_devices.copy()

    for new_device in current_devices:
        if not device_list_has(new_device, old_devices_copy):
            new_devices.append(new_device)

    if len(new_devices) != 0:
        print(
            colored(f"[?] {len(new_devices)} device(s) are new. These are: ", "yellow")
        )
        for count, dev in enumerate(new_devices):
            print(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
            print()
    else:
        print(colored("[?] No new devices found", "yellow"))

    # Looking for fixed/broken devices
    fixed_devices = []
    broken_devices = []

    for new_device in current_devices:
        chng_state = state_changed(new_device, old_devices)
        if chng_state == "not_found" or chng_state == "no_changes":
            continue

        if chng_state["to"] == True:
            fixed_devices.append(new_device)
        elif chng_state["to"] == False:
            broken_devices.append(new_device)

    if len(broken_devices) != 0:
        print(
            colored(
                f"[-] {len(broken_devices)} device(s) are broken since dump. These are: ",
                "red",
            )
        )
        for count, dev in enumerate(broken_devices):
            print(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
            print()
    else:
        print(colored("[+] No devices are broken since dump", "green"))

    if len(fixed_devices) != 0:
        print(
            colored(
                f"[+] {len(fixed_devices)} device(s) are fixed since dump. These are: ",
                "green",
            )
        )
        for count, dev in enumerate(fixed_devices):
            print(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
            print()
    else:
        print(colored("[-] No devices are fixed since dump", "red"))
