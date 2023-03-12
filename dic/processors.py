import subprocess, json
from dic.data import Device, Dump, DeclarativeBase
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import datetime, locale


class BaseProcessor:
    def __init__(self) -> None:
        self.engine = sqlalchemy.create_engine("sqlite:///deviceinfo.db")
        DeclarativeBase.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def __del__(self) -> None:
        self.session.close()
        self.engine.dispose()

    def remove_dump(self, dump_id: int):
        dumps = self.session.query(Dump).filter_by(id=dump_id)
        for rev in dumps:
            self.session.delete(rev)

        devices = self.session.query(Device).filter_by(dump_id=dump_id)
        for dev in devices:
            self.session.delete(dev)
        self.session.commit()

    def clear_dumps(self) -> None:
        dumps = self.session.query(Dump)
        for rev in dumps:
            self.session.delete(rev)

        devices = self.session.query(Device)
        for dev in devices:
            self.session.delete(dev)
        self.session.commit()

    def get_dump_list(self) -> list[tuple]:
        dumps = self.session.query(Dump)
        rev_list = []

        for rev in dumps:
            rev_list.append((rev.id, rev.datetime, rev.desc))

        return rev_list

    def get_devices_by_dump_id(self, dump_id) -> list[Device]:
        devices = self.session.query(Device).filter_by(dump_id=dump_id)
        if not devices or not self.session.query(Dump).filter_by(id=dump_id).first():
            raise Exception(f"No devices found by dump_id {dump_id}")
        return devices

    def get_devices_of_last_dump(self) -> list[Device]:
        dump = self.session.query(Dump).order_by(Dump.id.desc()).first()
        if not dump:
            raise Exception("No dumps found")
        return self.session.query(Device).filter_by(dump_id=dump.id)

    def get_current_devices(self) -> list[Device]:
        pass

    def dump_devices(self, dump_desc: str) -> Dump:
        pass


class WindowsProcessor(BaseProcessor):
    def get_current_devices(self) -> list[Device]:
        subprocess.run(
            [
                "PowerShell",
                "-Command",
                "[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8",
            ]
        )

        process_out = None
        process_out = subprocess.check_output(
            'PowerShell -Command "& {Get-PnpDevice -PresentOnly | Select-Object Status,Class,FriendlyName,InstanceId | ConvertTo-Json}"'
        )

        json_out = json.loads(process_out)

        device_list = []
        for json_device in json_out:
            status = True if json_device["Status"] == "OK" else False
            device = Device(
                device_id=json_device["InstanceId"],
                device_name=json_device["FriendlyName"],
                device_class=json_device["Class"],
                device_status=status,
                dump_id=None,
            )
            device_list.append(device)

        return device_list

    def dump_devices(self, dump_desc: str = "No description") -> Dump:
        dump = Dump(datetime=datetime.datetime.utcnow(), desc=dump_desc)
        self.session.add(dump)
        self.session.commit()
        self.session.refresh(dump)

        device_list = self.get_current_devices()
        for device in device_list:
            device.dump_id = dump.id
            self.session.add(device)
            self.session.commit()

        return dump
