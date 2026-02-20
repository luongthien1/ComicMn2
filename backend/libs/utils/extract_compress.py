import os
import tarfile
import zipfile
from pathlib import Path

from fastapi import UploadFile


def extract_file(file: UploadFile, dest: Path):
    temp_file_path = dest / f"temp_{file.filename}"
    os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
    with open(temp_file_path, "wb") as buffer:
        buffer.write(file.file.read())

    if is_zip(file):
        extract_zip(temp_file_path, dest)
    elif is_tar(file):
        extract_tar(temp_file_path, dest)

    temp_file_path.unlink()  # Remove the temporary archive file


def is_zip(file: UploadFile) -> bool:
    return file.filename.lower().endswith(".zip")


def is_tar(file: UploadFile) -> bool:
    return file.filename.lower().endswith((".tar", ".tar.gz", ".tgz"))


def extract_zip(file_path: Path, dest: Path):
    with zipfile.ZipFile(file_path) as z:
        z.extractall(dest)


def extract_tar(file_path: Path, dest: Path):
    with tarfile.open(file_path) as t:
        t.extractall(dest)
