import subprocess
import textwrap
from pathlib import Path

for GIT_BIN in [
    Path("/usr/bin/git"),
    Path(r"C:\Program Files\Git\bin\git.exe"),
    Path(r"C:\Program Files\Git\cmd\git.exe"),
]:
    if GIT_BIN.exists():
        break
else:
    raise RuntimeError("Could not find git binary")  # noqa: TRY003


def test_precommit_hook(datadir: Path) -> None:
    repo_dir = datadir

    # initialize git repo
    subprocess.run([GIT_BIN, "init"], cwd=repo_dir, check=True)
    subprocess.run(
        [GIT_BIN, "config", "user.name", "Test User"], cwd=repo_dir, check=True
    )
    subprocess.run(
        [GIT_BIN, "config", "user.email", "test@example.com"], cwd=repo_dir, check=True
    )
    subprocess.run(["pre-commit", "install"], cwd=repo_dir, check=True)  # noqa: S607

    # stage and commit without sync-with-uv
    subprocess.run([GIT_BIN, "add", "."], cwd=repo_dir, check=True)
    subprocess.run([GIT_BIN, "commit", "-m", "old hooks"], cwd=repo_dir, check=True)

    # add sync-with-uv
    hook_config = textwrap.dedent(
        """\
        - repo: local
          hooks:
        """
    )
    hook_config += textwrap.indent(
        Path(__file__).parents[1].joinpath(".pre-commit-hooks.yaml").read_text(), "  "
    )
    hook_config = textwrap.indent(hook_config, "  ")
    with repo_dir.joinpath(".pre-commit-config.yaml").open("a") as f:
        f.write(hook_config)

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
    expected_config = textwrap.dedent(
        """\
        repos:
          - repo: https://github.com/astral-sh/ruff-pre-commit
            rev: v0.1.0
            hooks:
              - id: ruff
        """
    )
    assert expected_config in updated_config

    # commit and succeed
    subprocess.run([GIT_BIN, "add", "."], cwd=repo_dir, check=True)
    subprocess.run([GIT_BIN, "commit", "-m", "new hooks"], cwd=repo_dir, check=True)
