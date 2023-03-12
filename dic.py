import platform, argparse, colorama
from dic.processors import *
from tabulate import tabulate
from dic.compare import compare_device_list


def main():
    system_name = platform.system()
    data_processor = None

    if system_name == "Windows":
        data_processor = WindowsProcessor()
        colorama.just_fix_windows_console()
    else:
        raise Exception(f"DIC can't work on {system_name} yet")

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-d", "--dump", help="create current devices dump and exit", action="store_true"
    )
    argparser.add_argument(
        "-r",
        "--remove",
        metavar="REV_ID",
        type=int,
        nargs=1,
        help="remove a dump with id specified",
    )
    argparser.add_argument(
        "-ca",
        "--clear-all",
        action="store_true",
        help="clear all dumps",
    )
    argparser.add_argument(
        "-l",
        "--list-dumps",
        action="store_true",
        help="print the list of all dumps",
    )
    argparser.add_argument(
        "-c",
        "--compare",
        action="store_true",
        help="compare current configuration with the newest dump",
    )
    args = argparser.parse_args()

    if args.dump:
        revision_info = data_processor.dump_devices()
        print(
            f"Dump with id {revision_info.id} was created successfully at {revision_info.datetime}"
        )
    elif args.remove:
        user_answer = input(
            f"Are you sure you want to delete dump #{args.remove[0]}? [y\\n]: "
        )
        if user_answer.lower().strip() == "y":
            data_processor.remove_dump(args.remove[0])
            print(f"Dump #{args.remove[0]} was removed successfully")
        print("Delete cancelled")
    elif args.clear_all:
        user_answer = input("Are you sure you want to delete all dumps? [y\\n]: ")
        if user_answer.lower().strip() == "y":
            data_processor.clear_dumps()
            print("All the dumps were deleted successfully")
        print("Delete cancelled")
    elif args.list_dumps:
        dump_data_list = data_processor.get_dump_list()

        if len(dump_data_list) == 0:
            print("Database has no dumps")
        elif len(dump_data_list) == 1:
            print(tabulate(dump_data_list, headers=("ID", "Datetime created")))
            print("\nDatabase has 1 dump in total")
        else:
            print(tabulate(dump_data_list, headers=("ID", "Datetime created")))
            print("\nDatabase has", len(dump_data_list), "dumps in total")
    elif args.compare:
        compare_device_list(
            data_processor.get_current_devices(),
            data_processor.get_devices_of_last_dump(),
        )


if __name__ == "__main__":
    main()
