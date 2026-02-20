import asyncio
import mimetypes
import os
from datetime import timedelta

from libs.file_system.utils import (
    S3_ACCESS_KEY_ID,
    S3_ENDPOINT_URL,
    S3_PRESIGNED_EXPIRE_HOURS,
    S3_REGION_NAME,
    S3_SECRET_ACCESS_KEY,
    S3_SECURE,
    S3File,
)
from libs.logger import logger
from minio import Minio, S3Error


class S3Object:
    def __init__(self, object_name: str, size: int, version_id: str, etag: str):
        self.object_name = object_name
        self.size = size
        self.version_id = version_id
        self.etag = etag


class TekoS3Client:

    def __init__(self):
        self.partner = "TEKO"
        self._public_enpoint = "s3.dev.teko.vn"
        self.s3_bucket = "carbon-drone-stitching-88336795-d458-40d8-b36c-194f565b2926"
        self._access_key = S3_ACCESS_KEY_ID
        self._secret_key = S3_SECRET_ACCESS_KEY
        self.s3_client = Minio(
            endpoint=S3_ENDPOINT_URL,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=S3_REGION_NAME,
            secure=S3_SECURE,
        )

    # you must use public client to generate signed url
    def get_public_client(self):
        return Minio(
            endpoint=self._public_enpoint,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=S3_REGION_NAME,
            secure=True,
        )

    def list_objects(self, prefix: str | None = None) -> list[dict]:
        objects = self.s3_client.list_objects(
            bucket_name=self.s3_bucket, prefix=prefix, recursive=True
        )
        buckets = [
            {
                "object_name": obj.object_name,
                "etag": obj.etag,
                "version_id": obj.version_id,
                "size": obj.size,
            }
            for obj in objects
        ]
        return buckets

    async def io_download_file(
        self, object_name: str, *, file_path: str, replace=False
    ):
        """Download a file from S3"""
        try:
            if os.path.exists(file_path):
                if replace:
                    logger.warning(f"Overwrite existing file: {file_path}")
                else:
                    logger.info(f"Skip existing file: {file_path}")
                    return

            logger.info(f"{object_name} downloading...")
            # Tránh block event loop (Minio là sync)
            await asyncio.to_thread(
                self.s3_client.fget_object,
                bucket_name=self.s3_bucket,
                object_name=object_name,
                file_path=file_path,
            )
            logger.info(
                "io_download_file successed",
                object_name=object_name,
                file_path=file_path,
                replace=replace,
            )
        except S3Error as e:
            logger.error(
                "io_download_file failed",
                object_name=object_name,
                file_path=file_path,
                replace=replace,
                error=e,
            )
            logger.error(f"Error downloading file {object_name}: {e}", exc_info=True)
            # Re-raise so caller can handle
            raise

    async def io_download_dir(
        self,
        sub_bucket: str,
        *,
        path_dest: str | None = None,
        replace: bool = False,
    ):
        """
        Download all files under sub_bucket (prefix) into a local directory.

        Args:
            sub_bucket: S3 prefix (folder) to download (e.g. 'foo/bar')
            path_dest: Local destination directory root. If provided, all objects
                       will be placed under this directory preserving the relative
                       structure inside sub_bucket. If not provided, a directory
                       named after sub_bucket (without trailing slash) is used.
        Returns:
            Absolute path of the local destination root directory.
        """
        normalized_sub_bucket = sub_bucket.rstrip("/") + "/"
        dest_root = (
            path_dest.rstrip("/\\") if path_dest else normalized_sub_bucket.rstrip("/")
        )
        os.makedirs(dest_root, exist_ok=True)

        logger.info(f"Destination dir: {dest_root} (prefix: {normalized_sub_bucket})")

        tasks: list[asyncio.Task] = []
        try:
            for obj in self.s3_client.list_objects(
                self.s3_bucket,
                prefix=normalized_sub_bucket,
                recursive=True,
            ):
                if obj.is_dir:
                    continue

                object_name = obj.object_name or ""
                # Relative path inside the prefix
                if not object_name.startswith(normalized_sub_bucket):
                    # Safety guard; skip unexpected items
                    continue

                rel_path = object_name[len(normalized_sub_bucket) :]
                if not rel_path:  # Skip if it's exactly the prefix marker
                    continue

                local_path = os.path.join(dest_root, rel_path)
                if not replace and os.path.exists(local_path):
                    continue

                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                tasks.append(
                    asyncio.create_task(
                        self.io_download_file(
                            object_name, file_path=local_path, replace=replace
                        )
                    )
                )

            if tasks:
                await asyncio.gather(*tasks)
            logger.info(
                "io_download_dir successed",
                sub_bucket=sub_bucket,
                file_path=path_dest,
                replace=replace,
            )
            return os.path.abspath(dest_root)

        except S3Error as e:
            logger.error(
                "io_download_dir failed",
                sub_bucket=sub_bucket,
                file_path=path_dest,
                replace=replace,
                error=e,
            )
            raise

    async def io_upload_file(
        self,
        file_path: str,
        *,
        object_name: str,
        replace: bool = True,
    ) -> S3File | None:
        """
        Upload a local file to S3.

        Args:
            file_path: Local file path.
            object_name: Destination object key.
            replace: If False, skip upload when object already exists.
        Returns:
            S3File
        Raises:
            FileNotFoundError, RuntimeError, S3Error
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")

        if not replace:
            try:
                # Check if object exists
                await asyncio.to_thread(
                    self.s3_client.stat_object, self.s3_bucket, object_name
                )
                logger.info(f"Skip existing object (replace=False): {object_name}")
                return None

            except S3Error:
                pass  # Not found -> continue

        guessed, _ = mimetypes.guess_type(file_path)
        content_type = guessed or "application/octet-stream"

        logger.info(f"Uploading {file_path} -> {object_name}")

        def _upload():
            return self.s3_client.fput_object(
                self.s3_bucket,
                object_name,
                file_path,
                content_type=content_type,
            )

        try:
            result = await asyncio.to_thread(_upload)
            logger.info(f"Uploaded {object_name}")
            return S3File(result)
        except S3Error as e:
            logger.error(
                "io_upload_file failed",
                object_name=object_name,
                file_path=file_path,
                replace=replace,
                error=e,
            )
            raise

    async def io_upload_dir(
        self,
        local_dir: str,
        *,
        prefix: str = "",
        replace: bool = True,
        concurrency: int = 10,
    ) -> list[S3File]:
        """
        Upload all files (recursively) under local_dir to S3.

        Args:
            local_dir: Local root directory.
            prefix: Optional S3 key prefix (folder) to prepend.
            replace: If False, skip objects that already exist.
            concurrency: Max concurrent uploads.

        Returns:
            List of S3File for successfully uploaded (or skipped when replace=True still returns uploaded only).
        """
        if not os.path.isdir(local_dir):
            raise FileNotFoundError(f"Directory not found: {local_dir}")

        norm_prefix = prefix.strip("/")

        def to_object_name(path: str) -> str:
            rel = os.path.relpath(path, local_dir)
            # Normalize to POSIX style for S3 keys
            rel = rel.replace(os.sep, "/")
            return f"{norm_prefix}/{rel}" if norm_prefix else rel

        semaphore = asyncio.Semaphore(concurrency)
        upload_tasks: list[asyncio.Task] = []

        for root, dirs, files in os.walk(local_dir):
            # Skip hidden directories
            if any(part.startswith(".") for part in root.split(os.sep)):
                continue
            # Filter out hidden dirs in-place (prevent descending into them)
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for fname in files:
                if fname.startswith("."):
                    continue
                file_path = os.path.join(root, fname)
                object_name = to_object_name(file_path)

                async def _one(fp=file_path, oname=object_name):
                    async with semaphore:
                        return await self.io_upload_file(
                            fp,
                            object_name=oname,
                            replace=replace,
                        )

                upload_tasks.append(asyncio.create_task(_one()))

        if not upload_tasks:
            logger.info("No files to upload.")
            return []

        results = await asyncio.gather(*upload_tasks, return_exceptions=True)

        uploaded: list[S3File] = []
        errors = 0
        for r in results:
            if isinstance(r, (Exception, BaseException)):
                errors += 1
            elif r is not None:
                uploaded.append(r)

        logger.info(
            "io_upload_dir",
            total_files=len(upload_tasks),
            uploaded=len(uploaded),
            errors={errors},
            skipped={len(upload_tasks) - len(uploaded) - errors},
        )
        return uploaded

    def get_object_from_uri(self, uri: str) -> str | None:
        uris = uri.replace("s3://", "").split("/")
        bucket = uris[0]
        valid = True
        if self.partner:
            valid = self.s3_bucket.lower() == bucket.lower()
        # check permission of partner
        if valid:
            return "/".join(uris[1:])
        return None

    # get presigned url
    def get_presigned_url(
        self, object_key: str, expiry_hours: int = S3_PRESIGNED_EXPIRE_HOURS
    ) -> str:
        url = self.get_public_client().presigned_get_object(
            bucket_name=self.s3_bucket,
            object_name=object_key,
            expires=timedelta(hours=expiry_hours),
        )
        return url

    def create_presigned_url(self, object_key: str, expiry_seconds: int = 300) -> str:
        """
        Tạo URL tạm thời (presigned URL) để upload một đối tượng (object) lên bucket S3 bằng phương thức PUT.

        Args:
            object_key (str): Khóa (key) của đối tượng trong bucket S3, tức là đường dẫn và tên file.
            expiry_seconds (int, optional): Thời gian tồn tại của URL tính bằng giây. Mặc định là 300 giây (5 phút).

        Returns:
            str: URL tạm thời cho phép upload file lên S3.

        Mô tả:
            Hàm sử dụng client public của S3 để tạo một presigned URL với thời gian hết hạn được chỉ định,
            giúp người dùng có thể upload file mà không cần quyền truy cập trực tiếp đến bucket.
        """
        url = self.get_public_client().presigned_put_object(
            bucket_name=self.s3_bucket,
            object_name=object_key,
            expires=timedelta(seconds=expiry_seconds),
        )
        return url
