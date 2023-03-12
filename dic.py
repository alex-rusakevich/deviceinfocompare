import platform, argparse
from dic.processors import *
from tabulate import tabulate


def main():
    system_name = platform.system()
    data_processor = None

    if system_name == "Windows":
        data_processor = WindowsProcessor()
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
        "-c",
        "--clear",
        action="store_true",
        help="clear all dumps",
    )
    argparser.add_argument(
        "-l",
        "--list-dumps",
        action="store_true",
        help="print the list of all dumps",
    )
    args = argparser.parse_args()

    if args.dump:
        revision_info = data_processor.dump_devices()
        print(
            f"Dump with id {revision_info.id} was created successfully at {revision_info.datetime}"
        )
    elif args.remove:
        data_processor.remove_dump(args.remove[0])
    elif args.clear:
        data_processor.clear_dumps()
    elif args.list_dumps:
        dump_data_list = data_processor.get_dump_list()

        print(tabulate(dump_data_list, headers=("ID", "Datetime created")))


if __name__ == "__main__":
    main()
