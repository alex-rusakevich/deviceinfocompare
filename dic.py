import platform
from dic.processors import *


def main():
    system_name = platform.system()
    data_processor = None

    if system_name == "Windows":
        data_processor = WindowsProcessor()

    data_processor.dump_devices()


if __name__ == "__main__":
    main()
