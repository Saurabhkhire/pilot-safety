"""
Resize and JPEG encode frames for Gemma 3n (keep under typical vision limits).
"""
from __future__ import annotations

import io
from typing import Optional

import cv2
import numpy as np

# Max dimension for model input (balance quality vs latency)
MAX_SIZE = 640
JPEG_QUALITY = 85


def encode_jpeg(frame: np.ndarray, max_size: int = MAX_SIZE, quality: int = JPEG_QUALITY) -> Optional[bytes]:
    """Resize if needed and encode as JPEG bytes."""
    if frame is None or frame.size == 0:
        return None
    h, w = frame.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        nw, nh = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok or buf is None:
        return None
    return buf.tobytes()
