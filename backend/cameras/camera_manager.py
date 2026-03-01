"""
Multi-camera capture — OpenCV face (A) and external (B).
Returns raw frames; frame_preprocessor can resize/JPEG for models.
Supports live camera (device index) or video file (path) for face source.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import cv2

from config import config

# Lazy open; avoid blocking import
_cap_face: Optional[cv2.VideoCapture] = None
_cap_external: Optional[cv2.VideoCapture] = None
# When set, use video file instead of camera device
_video_face_path: Optional[str] = None
_video_external_path: Optional[str] = None


def set_video_face_source(path: Optional[str]) -> None:
    """Set video file as face source. Call with None to switch back to camera."""
    global _cap_face, _video_face_path
    if _cap_face:
        _cap_face.release()
        _cap_face = None
    _video_face_path = path


def get_video_face_path() -> Optional[str]:
    """Return current video face source path, or None if using camera."""
    return _video_face_path


def set_video_external_source(path: Optional[str]) -> None:
    """Set video file as external/landing source. Call with None to switch back to camera."""
    global _cap_external, _video_external_path
    if _cap_external:
        _cap_external.release()
        _cap_external = None
    _video_external_path = path


def get_video_external_path() -> Optional[str]:
    """Return current video external source path, or None if using camera."""
    return _video_external_path


def _get_face_cap() -> Optional[cv2.VideoCapture]:
    global _cap_face
    if _cap_face is not None:
        if _cap_face.isOpened():
            return _cap_face
        # Video ended or error — release and reopen (loop for video files)
        _cap_face.release()
        _cap_face = None
    if _video_face_path and Path(_video_face_path).exists():
        _cap_face = cv2.VideoCapture(_video_face_path)
        return _cap_face if _cap_face.isOpened() else None
    _cap_face = cv2.VideoCapture(config.camera_face_index)
    return _cap_face if (_cap_face and _cap_face.isOpened()) else None


def _get_external_cap() -> Optional[cv2.VideoCapture]:
    global _cap_external
    if _cap_external is not None:
        if _cap_external.isOpened():
            return _cap_external
        _cap_external.release()
        _cap_external = None
    if _video_external_path and Path(_video_external_path).exists():
        _cap_external = cv2.VideoCapture(_video_external_path)
        return _cap_external if _cap_external.isOpened() else None
    _cap_external = cv2.VideoCapture(config.camera_external_index)
    return _cap_external if (_cap_external and _cap_external.isOpened()) else None


def get_frame_face() -> Optional[str]:
    """
    Read one frame from face camera or video file, return base64 JPEG or None.
    Used by PerceptionAgent when no frame_b64 is passed.
    Video files loop when they end.
    """
    cap = _get_face_cap()
    if cap is None:
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        # Video ended — loop if it's a file
        if _video_face_path:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        if not ok or frame is None:
            return None
    from cameras.frame_preprocessor import encode_jpeg
    jpeg_bytes = encode_jpeg(frame)
    if not jpeg_bytes:
        return None
    return base64.b64encode(jpeg_bytes).decode("ascii")


def get_frame_external() -> Optional[str]:
    """Read one frame from external/belly cam or video file, return base64 JPEG or None. Video loops when done."""
    cap = _get_external_cap()
    if cap is None:
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        if _video_external_path:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        if not ok or frame is None:
            return None
    from cameras.frame_preprocessor import encode_jpeg
    jpeg_bytes = encode_jpeg(frame)
    if not jpeg_bytes:
        return None
    return base64.b64encode(jpeg_bytes).decode("ascii")


def release_all() -> None:
    global _cap_face, _cap_external, _video_face_path, _video_external_path
    _video_face_path = None
    _video_external_path = None
    if _cap_face:
        _cap_face.release()
        _cap_face = None
    if _cap_external:
        _cap_external.release()
        _cap_external = None
