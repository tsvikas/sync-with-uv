import importlib

import sync_with_uv


def test_version() -> None:
    assert importlib.metadata.version("sync_with_uv") == sync_with_uv.__version__
