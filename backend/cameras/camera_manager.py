"""
Multi-camera capture — OpenCV face (A) and external (B).
Returns raw frames; frame_preprocessor can resize/JPEG for models.
"""
from __future__ import annotations

import base64
import io
from typing import Optional

import cv2

from config import config

# Lazy open; avoid blocking import
_cap_face: Optional[cv2.VideoCapture] = None
_cap_external: Optional[cv2.VideoCapture] = None


def _get_face_cap() -> Optional[cv2.VideoCapture]:
    global _cap_face
    if _cap_face is None:
        _cap_face = cv2.VideoCapture(config.camera_face_index)
    return _cap_face if (_cap_face and _cap_face.isOpened()) else None


def _get_external_cap() -> Optional[cv2.VideoCapture]:
    global _cap_external
    if _cap_external is None:
        _cap_external = cv2.VideoCapture(config.camera_external_index)
    return _cap_external if (_cap_external and _cap_external.isOpened()) else None


def get_frame_face() -> Optional[str]:
    """
    Read one frame from face camera, return base64 JPEG or None.
    Used by PerceptionAgent when no frame_b64 is passed.
    """
    cap = _get_face_cap()
    if cap is None:
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    from cameras.frame_preprocessor import encode_jpeg
    jpeg_bytes = encode_jpeg(frame)
    if not jpeg_bytes:
        return None
    return base64.b64encode(jpeg_bytes).decode("ascii")


def get_frame_external() -> Optional[str]:
    """Read one frame from external/belly cam, return base64 JPEG or None."""
    cap = _get_external_cap()
    if cap is None:
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    from cameras.frame_preprocessor import encode_jpeg
    jpeg_bytes = encode_jpeg(frame)
    if not jpeg_bytes:
        return None
    return base64.b64encode(jpeg_bytes).decode("ascii")


def release_all() -> None:
    global _cap_face, _cap_external
    if _cap_face:
        _cap_face.release()
        _cap_face = None
    if _cap_external:
        _cap_external.release()
        _cap_external = None
