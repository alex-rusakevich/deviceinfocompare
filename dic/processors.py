import subprocess, json
from dic.data import Device, Revision, DeclarativeBase
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

    def get_devices(self) -> list[Device]:
        pass

    def dump_devices(self) -> None:
        pass


class WindowsProcessor(BaseProcessor):
    def get_devices(self) -> list[Device]:
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
                revision=None,
            )
            device_list.append(device)

        return device_list

    def dump_devices(self) -> None:
        revision = Revision(datetime=datetime.datetime.utcnow())
        self.session.add(revision)
        self.session.commit()
        self.session.refresh(revision)

        device_list = self.get_devices()
        for device in device_list:
            device.revision = revision.id
            self.session.add(device)
            self.session.commit()
