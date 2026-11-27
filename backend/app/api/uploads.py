from fastapi import HTTPException, UploadFile

ICON_UPLOAD_LIMIT_BYTES = 2_000_000
BANNER_UPLOAD_LIMIT_BYTES = 10 * 1024 * 1024
_CHUNK_SIZE = 64 * 1024


async def read_upload(
    upload: UploadFile | None,
    limit_bytes: int,
    label: str,
    limit_label: str,
) -> tuple[str | None, str | None, bytes | None]:
    """Read a bounded upload instead of buffering an unlimited request body."""
    if upload is None or not upload.filename:
        return None, None, None

    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(_CHUNK_SIZE):
        total += len(chunk)
        if total > limit_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{label} file is too large (max {limit_label}).",
            )
        chunks.append(chunk)
    return upload.filename, upload.content_type, b"".join(chunks)


async def read_icon_upload(
    upload: UploadFile | None,
) -> tuple[str | None, str | None, bytes | None]:
    return await read_upload(upload, ICON_UPLOAD_LIMIT_BYTES, "Icon", "2 MB")


async def read_banner_upload(
    upload: UploadFile | None,
) -> tuple[str | None, str | None, bytes | None]:
    return await read_upload(upload, BANNER_UPLOAD_LIMIT_BYTES, "Banner", "10 MB")
