from datetime import datetime

from app.config.models import DeviceConfig
from app.core.dedupe import Deduplicator
from app.core.devices import DeviceRegistry
from app.normalizers.rtl433 import NormalizedFrame, normalize, parse_line


class Rtl433FrameProcessor:
    def __init__(
        self,
        devices: list[DeviceConfig],
        site_timezone: str,
        dedupe_window_seconds: float = 5,
    ) -> None:
        self._registry = DeviceRegistry(devices)
        self._site_timezone = site_timezone
        self._deduplicator = Deduplicator(
            window_seconds=dedupe_window_seconds
        )

    def process_line(
        self,
        line: str,
        received_at: datetime,
    ) -> NormalizedFrame | None:
        raw_frame = parse_line(line)
        frame = normalize(raw_frame, self._site_timezone, received_at)

        if self._registry.get(frame.device_key) is None:
            return None
        if self._deduplicator.is_duplicate(frame):
            return None

        return frame
