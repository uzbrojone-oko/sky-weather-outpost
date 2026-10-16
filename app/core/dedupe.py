import json
from datetime import timedelta


class Deduplicator:
    def __init__(self, window_seconds: float = 5) -> None:
        if window_seconds < 0:
            raise ValueError("window_seconds must be non-negative")

        self._window = timedelta(seconds=window_seconds)
        self._seen: dict[tuple[str, str], object] = {}

    def is_duplicate(self, frame: object) -> bool:
        fingerprint = self._fingerprint(frame)
        measured_at = frame.measured_at or frame.received_at
        previous_time = self._seen.get(fingerprint)

        if (
            previous_time is not None
            and abs(measured_at - previous_time) <= self._window
        ):
            return True

        self._seen[fingerprint] = measured_at
        return False

    @staticmethod
    def _fingerprint(frame: object) -> tuple[str, str]:
        measurements = [
            {
                "metric": measurement.metric,
                "value": measurement.value,
                "unit": measurement.unit,
            }
            for measurement in frame.measurements
        ]
        measurements.sort(key=lambda item: (item["metric"], item["unit"] or ""))

        normalized_measurements = json.dumps(
            measurements,
            sort_keys=True,
            separators=(",", ":"),
        )
        return frame.device_key, normalized_measurements
