from app.config.models import DeviceConfig


class DeviceRegistry:
    def __init__(self, devices: list[DeviceConfig]) -> None:
        self._devices_by_key = {device.key: device for device in devices}

    def get(self, device_key: str) -> DeviceConfig | None:
        return self._devices_by_key.get(device_key)
