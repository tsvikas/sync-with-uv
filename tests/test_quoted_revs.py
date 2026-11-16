"""YAML quotes are syntax, not part of the revision being synchronized."""

import subprocess
import sys
from pathlib import Path

import pytest

from sync_with_uv.cli import app
from sync_with_uv.sync_with_uv import process_config_text


@pytest.mark.parametrize("quote", ["'", '"'])
@pytest.mark.parametrize("current", ["v1.4.0", "v1.5.0"])
@pytest.mark.parametrize("ending", ["\n", "\r\n", ""])
def test_quoted_revision_preserves_prefix_and_format(
    quote: str, current: str, ending: str
) -> None:
    config = (
        "repos:\n"
        "- repo: https://github.com/asottile/yesqa\n"
        f"  rev: {quote}{current}{quote}  # keep this comment{ending}"
    )
    result, changes = process_config_text(
        config, {"yesqa": "1.5.0"}, config_format="yaml"
    )
    assert result == config.replace(current, "v1.5.0")
    assert changes.repos == {
        "yesqa": True if current == "v1.5.0" else (current, "v1.5.0")
    }


@pytest.mark.parametrize("quote", ["'", '"'])
@pytest.mark.parametrize("custom_template", [False, True])
def test_quoted_revision_uses_configured_template(
    quote: str, *, custom_template: bool
) -> None:
    repo = "https://github.com/psf/black"
    config = f"repos:\n- repo: {repo}\n  rev: {quote}22.1.0{quote}\n"
    template = {repo: "release-${version}"} if custom_template else None
    target = "release-23.1.0" if custom_template else "23.1.0"
    result, changes = process_config_text(
        config,
        {"black": "23.1.0"},
        config_format="yaml",
        user_version_mappings=template,
    )
    assert result == config.replace("22.1.0", target)
    assert changes.repos == {"black": ("22.1.0", target)}


@pytest.mark.parametrize("quote", ["'", '"'])
def test_numeric_revision_remains_a_string(tmp_path: Path, quote: str) -> None:
    config = (
        "repos:\n"
        "- repo: https://github.com/example/tool\n"
        f"  rev: {quote}1.0{quote}\n"
        "  hooks:\n"
        "    - id: tool\n"
    )
    result, _ = process_config_text(config, {"tool": "1.1"}, config_format="yaml")
    path = tmp_path / ".pre-commit-config.yaml"
    path.write_text(result)
    subprocess.run(
        [sys.executable, "-m", "pre_commit", "validate-config", str(path)],
        check=True,
        capture_output=True,
    )
    assert result == config.replace("1.0", "1.1")


@pytest.mark.parametrize("flags", [[], ["--check"], ["--diff"]])
def test_quoted_revision_cli_is_idempotent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], flags: list[str]
) -> None:
    config = tmp_path / ".pre-commit-config.yaml"
    original = (
        b"repos:\n"
        b"- repo: https://github.com/asottile/yesqa\n"
        b"  rev: 'v1.5.0'  # already at the locked version\n"
        b"  hooks:\n"
        b"    - id: yesqa\n"
    )
    config.write_bytes(original)
    lock = tmp_path / "uv.lock"
    lock.write_text('[[package]]\nname = "yesqa"\nversion = "1.5.0"\n')
    for _ in range(2):
        with pytest.raises(SystemExit) as exc_info:
            app(["-p", str(config), "-u", str(lock), *flags])
        assert exc_info.value.code == 0
        assert config.read_bytes() == original
        captured = capsys.readouterr()
        assert "1 package" in captured.err
        assert "0 packages" in captured.err
        assert "@@" not in captured.out


@pytest.mark.parametrize("quote", ["'", '"'])
def test_toml_revision_quoting_still_works(quote: str) -> None:
    config = (
        "[[repos]]\n"
        'repo = "https://github.com/asottile/yesqa"\n'
        f"rev = {quote}v1.4.0{quote} # keep this comment\n"
    )
    result, changes = process_config_text(
        config, {"yesqa": "1.5.0"}, config_format="toml"
    )
    assert result == config.replace("v1.4.0", "v1.5.0")
    assert changes.repos == {"yesqa": ("v1.4.0", "v1.5.0")}


@pytest.mark.parametrize("current", ["v1.4.0'branch", 'v1.4.0"branch'])
def test_plain_revision_with_internal_quote_is_replaced_whole(current: str) -> None:
    config = f"repos:\n- repo: https://github.com/asottile/yesqa\n  rev: {current}\n"
    result, changes = process_config_text(
        config, {"yesqa": "1.5.0"}, config_format="yaml"
    )
    assert result == config.replace(current, "v1.5.0")
    assert changes.repos == {"yesqa": (current, "v1.5.0")}
