from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from app.ingest.rtl433 import Rtl433FrameProcessor
from app.normalizers.rtl433 import NormalizedFrame


def replay_jsonl(
    path: Path,
    processor: Rtl433FrameProcessor,
    received_at: datetime,
) -> Iterator[NormalizedFrame]:
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            frame = processor.process_line(line, received_at)
            if frame is not None:
                yield frame
