from datetime import datetime
from enum import Enum
from pathlib import Path

from minio.helpers import ObjectWriteResult

S3_ACCESS_KEY_ID = "DUWEY9DDRLF05C8B37TG"
S3_BUCKET_NAME = "carbon-drone-stitching-88336795-d458-40d8-b36c-194f565b2926"
S3_ENDPOINT_URL = "s3.dev.teko.vn"
S3_REGION_NAME = "vn-north-1"
S3_SECRET_ACCESS_KEY = "4BTtiwzXs3INnGa5cblCwgJUkKkcaU8o2RuZxtmF"
S3_SECURE = True
S3_PRESIGNED_EXPIRE_HOURS = 24
ROOT_FOLDER = "data"


class S3File:
    bucket: str
    object_name: str
    etag: str | None
    version_id: str | None
    last_modified: datetime | None

    def __init__(self, obj_result: ObjectWriteResult):
        self.bucket = obj_result.bucket_name
        self.object_name = obj_result.object_name
        self.etag = obj_result.etag
        self.version_id = obj_result.version_id
        self.last_modified = obj_result.last_modified

    def to_url(self):
        return f"s3://{self.bucket}/{self.object_name}"

    def to_str(self):
        return (
            "object_name: {}, etag: {}, version-id: {}".format(
                self.object_name,
                self.etag,
                self.version_id,
            ),
        )


class S3SubBucket(str, Enum):
    KARBON_MODEL = "karbon_ai"
    KML_FILE = "sample_kml"
    TIF_FILE = "sample_tif"
    SHAPE_FILE = "sample_shapefile"
    IMAGE = "sample_img"
    AUDIO = "sample_audio"
    VIDEO = "sample_video"
    MASTER_DATA = "master_data"
    RESOURCE_DATA = "resource_data"

    def to_s3_folder(self, sub_path: str | None = None, *args) -> str:
        s3_path = f"{self.value}/{sub_path}" if sub_path else self.value
        # ex: partner = WILD_ASIA => p_path = WILD_ASIA/sample_tif/....
        return s3_path

    def to_local_path(self, sub_path: str | None = None, *args) -> Path:
        # ex: partner = WILD_ASIA => p_path = WILD_ASIA/sample_tif/....
        p_path = self.value
        data_path = Path(ROOT_FOLDER) / p_path
        return data_path / sub_path if sub_path else data_path
