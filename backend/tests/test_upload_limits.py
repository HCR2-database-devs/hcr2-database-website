import asyncio
import io
from typing import cast

import pytest
from fastapi import HTTPException, UploadFile

from app.api.uploads import (
    ICON_UPLOAD_LIMIT_BYTES,
    read_banner_upload,
    read_icon_upload,
)


class FakeUpload:
    def __init__(self, content: bytes) -> None:
        self.filename = "image.webp"
        self.content_type = "image/webp"
        self._stream = io.BytesIO(content)

    async def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)


def test_icon_upload_at_limit_is_read() -> None:
    content = b"x" * ICON_UPLOAD_LIMIT_BYTES

    assert asyncio.run(read_icon_upload(cast(UploadFile, FakeUpload(content)))) == (
        "image.webp",
        "image/webp",
        content,
    )


def test_icon_upload_over_limit_is_rejected_before_buffering() -> None:
    upload = FakeUpload(b"x" * (10 * 1024 * 1024))

    with pytest.raises(HTTPException) as error:
        asyncio.run(read_icon_upload(cast(UploadFile, upload)))

    assert error.value.status_code == 413
    assert "Icon file is too large" in str(error.value.detail)
    assert upload._stream.tell() < 10 * 1024 * 1024


def test_banner_upload_over_limit_is_rejected() -> None:
    content = b"x" * (10 * 1024 * 1024 + 1)

    with pytest.raises(HTTPException) as error:
        asyncio.run(read_banner_upload(cast(UploadFile, FakeUpload(content))))

    assert error.value.status_code == 413
    assert "Banner file is too large" in str(error.value.detail)
