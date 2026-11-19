"""scripts/check_release_floor.py: publish.yml refuses to publish while the crud-views floor is below 1.0.0rc1."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_release_floor.py"


def run(pyproject: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(pyproject)], capture_output=True, text=True)


@pytest.mark.parametrize(
    ("spec", "ok"),
    [
        ("django-crud-views>=0.30", False),
        ("django-crud-views (>=0.30)", False),
        ("django-crud-views>=1.0.0rc1", True),
        ("django-crud-views>=1.0.0", True),
        ("django-crud-views (>=1.0.0rc1)", True),
        ("django-crud-views>=1.0.0rc1,<2", True),
        ("django-crud-views", False),
    ],
)
def test_release_floor(tmp_path, spec, ok):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'[project]\nname = "x"\ndependencies = ["django>=5.2", "{spec}"]\n')
    result = run(pyproject)
    assert result.returncode == (0 if ok else 1), result.stdout + result.stderr
    if not ok:
        assert "django-crud-views" in result.stdout + result.stderr


def test_missing_requirement_fails(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\ndependencies = ["django>=5.2"]\n')
    assert run(pyproject).returncode == 1


def test_repository_is_not_releasable_yet():
    # Until django-crud-views 1.0.0rc1 is on PyPI the floor stays at 0.30; the release commit raises it and flips this.
    assert run(ROOT / "pyproject.toml").returncode == 1


GIT_LINE = "django-crud-views @ git+https://github.com/jacob-consulting/django-crud-views@main\n"


def releasable_project(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "x"\ndependencies = ["django-crud-views>=1.0.0rc1"]\n')
    return pyproject


def test_git_install_in_noxfile_fails(tmp_path):
    # The floor is raised, but the matrix would still test crud-views' GitHub main, not what PyPI users install.
    pyproject = releasable_project(tmp_path)
    (tmp_path / "noxfile.py").write_text(f'CRUD_VIEWS = "{GIT_LINE.strip()}"\n')
    result = run(pyproject)
    assert result.returncode == 1
    assert "noxfile.py" in result.stdout


def test_git_install_in_demo_requirements_fails(tmp_path):
    pyproject = releasable_project(tmp_path)
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "demo.txt").write_text("gunicorn>=23\n" + GIT_LINE)
    result = run(pyproject)
    assert result.returncode == 1
    assert "demo.txt" in result.stdout


def test_released_dependency_files_pass(tmp_path):
    pyproject = releasable_project(tmp_path)
    (tmp_path / "noxfile.py").write_text("import nox\n")
    (tmp_path / "requirements").mkdir()
    (tmp_path / "requirements" / "demo.txt").write_text("gunicorn>=23\n")
    assert run(pyproject).returncode == 0
