import pytest

from sync_with_uv.repo_data import repo_to_package, repo_to_version_template


@pytest.mark.parametrize(
    ("url", "package"),
    [
        ("https://github.com/psf/black-pre-commit-mirror", "black"),
        ("https://github.com/psf/black", "black"),
        ("https://github.com/astral-sh/ruff-pre-commit", "ruff"),
        ("https://github.com/unknown/repo", "repo"),
    ],
)
def test_repo_to_package(url: str, package: str) -> None:
    assert repo_to_package(url) == package


def test_local_repo_to_package() -> None:
    assert repo_to_package("local") is None


@pytest.mark.parametrize(
    ("url", "version_template"),
    [
        ("https://github.com/psf/black-pre-commit-mirror", "${rev}"),
        ("https://github.com/psf/black", "${rev}"),
        ("https://github.com/astral-sh/ruff-pre-commit", "v${rev}"),
    ],
)
def test_repo_to_version_template(url: str, version_template: str) -> None:
    # Test known repos
    assert repo_to_version_template(url) == version_template


def test_unknown_repo_to_version_template() -> None:
    assert repo_to_version_template("https://github.com/unknown/repo") is None
