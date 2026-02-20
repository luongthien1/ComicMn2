import os

import magic


def detect_media_type_magic(path: str) -> str:
    mime = magic.from_file(path, mime=True)

    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"

    return "unknown"


def get_folder_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            fp = os.path.join(root, name)
            if not os.path.islink(fp):  # tránh double-count symlink
                total += os.path.getsize(fp)
    return total
