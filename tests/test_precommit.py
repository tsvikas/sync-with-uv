import subprocess
import textwrap
from pathlib import Path

import pytest

for GIT_BIN in [
    Path("/usr/bin/git"),
    Path(r"C:\Program Files\Git\bin\git.exe"),
    Path(r"C:\Program Files\Git\cmd\git.exe"),
]:
    if GIT_BIN.exists():
        break
else:
    raise RuntimeError("Could not find git binary")  # noqa: TRY003


@pytest.fixture
def repo_with_precommit(tmp_path: Path) -> Path:
    ruff = ("v0.0.200", "0.1.0")
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run([GIT_BIN, "init"], cwd=repo_dir, check=True)
    subprocess.run(
        [GIT_BIN, "config", "user.name", "Test User"], cwd=repo_dir, check=True
    )
    subprocess.run(
        [GIT_BIN, "config", "user.email", "test@example.com"], cwd=repo_dir, check=True
    )
    repo_dir.joinpath(".pre-commit-config.yaml").write_text("repos:\n")
    repo_dir.joinpath("uv.lock").write_text("version = 1\nrequires = []\n")
    subprocess.run(["pre-commit", "install"], cwd=repo_dir, check=True)  # noqa: S607
    if ruff:
        repo_dir.joinpath("dummy_module.py").write_text('print("Hello, world!")\n')
        with repo_dir.joinpath("pyproject.toml").open("a") as f:
            f.write('[tool.ruff]\ntarget-version = "py311"\n')
        with repo_dir.joinpath("uv.lock").open("a") as f:
            f.write(f'[[package]]\nname = "ruff"\nversion = "{ruff[1]}"\n')
        with repo_dir.joinpath(".pre-commit-config.yaml").open("a") as f:
            f.write(
                "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
                f"    rev: {ruff[0]}\n"
                "    hooks:\n"
                "      - id: ruff\n"
            )
    # stage and commit without sync-with-uv
    subprocess.run([GIT_BIN, "add", "."], cwd=repo_dir, check=True)
    subprocess.run([GIT_BIN, "commit", "-m", "old hooks"], cwd=repo_dir, check=True)

    return repo_dir


THIS_REPO_HOOKS = (
    textwrap.dedent(
        """\
        - repo: local
          hooks:
        """
    )
    + textwrap.indent(
        Path(__file__).parents[1].joinpath(".pre-commit-hooks.yaml").read_text(), "  "
    )
)


def test_precommit_hook(repo_with_precommit: Path) -> None:
    repo_dir = repo_with_precommit

    # add sync-with-uv
    with repo_dir.joinpath(".pre-commit-config.yaml").open("a") as f:
        f.write(textwrap.indent(THIS_REPO_HOOKS, "  "))

    # commit and fail
    subprocess.run([GIT_BIN, "add", "."], cwd=repo_dir, check=True, capture_output=True)
    commit_process = subprocess.run(  # noqa: PLW1510
        [GIT_BIN, "commit", "-m", "failing commit"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    assert commit_process.returncode == 1
    assert ".....Failed" in commit_process.stderr

    # check the updated .pre-commit-config.yaml
    updated_config_path = repo_dir / ".pre-commit-config.yaml"
    updated_config = updated_config_path.read_text()
    expected_config = textwrap.indent(
        textwrap.dedent(
            """\
          - repo: https://github.com/astral-sh/ruff-pre-commit
            rev: v0.1.0
            hooks:
              - id: ruff
        """
        ),
        "  ",
    )
    assert expected_config in updated_config

    # commit and succeed
    subprocess.run([GIT_BIN, "add", "."], cwd=repo_dir, check=True)
    subprocess.run([GIT_BIN, "commit", "-m", "new hooks"], cwd=repo_dir, check=True)
