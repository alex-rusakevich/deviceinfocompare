import logging

logger = logging.getLogger(__name__)


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
        device_total_change = "(" + f"+{device_total_change}" + ")"
    else:
        device_total_change = "(" + f"{device_total_change}" + ")"

    logger.info(f"Previous device amount is {len(old_devices)}")
    if device_total_change == "":
        logger.info(f"[+] Current device amount is {len(current_devices)} too")
    elif "+" in device_total_change:
        logger.info(
            f"[?] Current device amount is {len(current_devices)} {device_total_change}"
        )
    else:
        logger.info(
            f"[-] Current device amount is {len(current_devices)} {device_total_change}"
        )

    # Looking for missing devices
    missing_devices = []

    current_devices_copy = current_devices.copy()

    for old_device in old_devices:
        if not device_list_has(old_device, current_devices_copy):
            missing_devices.append(old_device)

    if len(missing_devices) != 0:
        logger.info(
            f"[-] {len(missing_devices)} device(s) are missing. These are: ",
        )
        for count, dev in enumerate(missing_devices):
            logger.info(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
    else:
        logger.info("[+] No devices are missing, hooray!")

    # Looking for new devices
    new_devices = []

    old_devices_copy = old_devices.copy()

    for new_device in current_devices:
        if not device_list_has(new_device, old_devices_copy):
            new_devices.append(new_device)

    if len(new_devices) != 0:
        logger.info(f"[?] {len(new_devices)} device(s) are new. These are: ")
        for count, dev in enumerate(new_devices):
            logger.info(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
    else:
        logger.info("[?] No new devices found")

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
        logger.info(
            f"[-] {len(broken_devices)} device(s) are broken since dump. These are: "
        )
        for count, dev in enumerate(broken_devices):
            logger.info(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
    else:
        logger.info("[+] No devices are broken since dump")

    if len(fixed_devices) != 0:
        logger.info(
            f"[+] {len(fixed_devices)} device(s) are fixed since dump. These are: "
        )
        for count, dev in enumerate(fixed_devices):
            logger.info(
                f"{count + 1}. {dev.device_name} [{dev.device_class}]\n{dev.device_id}"
            )
    else:
        logger.info("[-] No devices are fixed since dump")
