import subprocess
import textwrap
from pathlib import Path


def test_precommit_hook(datadir: Path) -> None:
    """
    Tests that the pre-commit hook runs successfully, updates versions,
    and the commit proceeds.
    """
    repo_dir = datadir

    # initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True
    )
    subprocess.run(["pre-commit", "install"], cwd=repo_dir, check=True)

    # stage and commit without sync-with-uv
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    commit_process1 = subprocess.run(["git", "commit", "-m", "old hooks"], cwd=repo_dir)
    assert commit_process1.returncode == 0

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
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    commit_process2 = subprocess.run(
        ["git", "commit", "-m", "failing commit"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    assert commit_process2.returncode == 1
    assert ".....Failed" in commit_process2.stderr

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
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    commit_process3 = subprocess.run(["git", "commit", "-m", "new hooks"], cwd=repo_dir)
    assert commit_process3.returncode == 0
