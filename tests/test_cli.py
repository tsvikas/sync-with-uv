from typer.testing import CliRunner

from sync_with_uv import __version__
from sync_with_uv.cli import app

runner = CliRunner()


def test_app_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
