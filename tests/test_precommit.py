import subprocess
from pathlib import Path
import yaml

def test_precommit_hook_runs_successfully(shared_datadir: Path) -> None:
    """
    Tests that the pre-commit hook runs successfully, updates versions,
    and the commit proceeds.
    """
    repo_dir = shared_datadir

    # Initialize Git repository
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    # Set up user name and email for git commit
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)


    # Install pre-commit hooks
    # We need to tell pre-commit where to find the local hook.
    # The hook is defined in .pre-commit-hooks.yaml in the *project root*,
    # not in the test directory.
    # We can create a symlink or copy, but simpler to run pre-commit with --hook-type pre-commit
    # and ensure that the `sync-with-uv` command is available in the PATH.
    # For this test, we assume `sync-with-uv` is installed and in PATH,
    # which would be the case if `hatch run test:test` or `just test` is used.
    subprocess.run(["pre-commit", "install"], cwd=repo_dir, check=True, capture_output=True)

    # Stage files
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)

    # Commit
    commit_process = subprocess.run(
        ["git", "commit", "-m", "Test commit"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )

    # Assert commit was successful
    assert commit_process.returncode == 0, \
        f"Commit failed. stdout: {commit_process.stdout}, stderr: {commit_process.stderr}"

    # Read the updated .pre-commit-config.yaml
    updated_config_path = repo_dir / ".pre-commit-config.yaml"
    assert updated_config_path.exists(), ".pre-commit-config.yaml not found after commit"

    with open(updated_config_path, "r") as f:
        updated_config = yaml.safe_load(f)

    # Assert ruff version was updated
    ruff_updated = False
    for repo in updated_config.get("repos", []):
        if repo.get("repo") == "https://github.com/astral-sh/ruff-pre-commit":
            assert repo.get("rev") == "v0.1.0", \
                f"Ruff version not updated. Expected v0.1.0, got {repo.get('rev')}"
            ruff_updated = True
            break
    
    assert ruff_updated, "Ruff configuration not found in .pre-commit-config.yaml"
