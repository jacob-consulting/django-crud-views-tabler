"""Test matrix, ported from django-crud-views' noxfile.py.

Every session installs the built distribution, never the checkout, so packaging defects (missing templates, static
files, modules) fail the tests. Local day-to-day runs use `task test` against the sibling checkouts instead.
"""

import nox

PYTHON_VERSIONS = ["3.12", "3.13", "3.14", "3.15"]
# The LTS and the latest release only.
DJANGO_VERSIONS = ["5.2", "6.1"]

# The theme tracks django-crud-views features that are not on PyPI yet. Remove this (here and in
# requirements/demo.txt) once django-crud-views 1.0.0rc1 is released, and raise the floor in pyproject.toml to
# >=1.0.0rc1 (scripts/check_release_floor.py guards publish.yml until then).
CRUD_VIEWS = (
    "django-crud-views[workflow,polymorphic,guardian,ordered]"
    " @ git+https://github.com/jacob-consulting/django-crud-views@main"
)

# Both packages must come from site-packages, not from src/ on the path.
_INSTALLED_PROJECT_ORIGIN = """
from pathlib import Path
import sysconfig
import crud_views_tabler
import django_tabler

paths = sysconfig.get_paths()
for module in (crud_views_tabler, django_tabler):
    origin = Path(module.__file__).resolve()
    print(f"Installed {module.__name__}: {origin}")
    assert any(origin.is_relative_to(Path(paths[key]).resolve()) for key in ("purelib", "platlib")), origin
    assert not origin.is_relative_to(Path("src").resolve()), origin
"""

# Each package suite has its own settings module.
SUITES = [
    ("tests/crispy_tabler", "tests.crispy_tabler.settings"),
    ("tests/crud_views_tabler", "tests.crud_views_tabler.settings"),
    ("tests/django_tabler", "tests.django_tabler.settings"),
]


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
@nox.parametrize("django", DJANGO_VERSIONS)
def tests(session, django):
    # One resolver transaction, so the git django-crud-views is the one installed. --no-sources: ignore the sibling
    # checkouts of [tool.uv.sources], as CI and pip users do.
    session.install("--no-sources", f"django~={django}.0", CRUD_VIEWS, ".[test]")

    env = {"PYTHONPATH": ""}
    session.run("python", "-c", _INSTALLED_PROJECT_ORIGIN, env=env)

    # One XML report per session: all sessions run from the repo root and would overwrite a shared coverage.xml.
    session.run("coverage", "erase", env=env)
    for index, (path, settings) in enumerate(SUITES):
        report = (
            [f"--cov-report=xml:coverage-py{session.python}-dj{django}.xml", "--cov-report=term-missing"]
            if index == len(SUITES) - 1
            else ["--cov-report="]
        )
        session.run(
            "pytest", path, "--ds", settings, "-n", "auto", "--cov", "--cov-append", *report, *session.posargs, env=env
        )


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
@nox.parametrize("django", DJANGO_VERSIONS)
def examples(session, django):
    # requirements/demo.txt too: proves the Render build's requirements resolve together with the package.
    session.install(
        "--no-sources", f"django~={django}.0", CRUD_VIEWS, ".[examples,test]", "-r", "requirements/demo.txt"
    )

    env = {"PYTHONPATH": ""}
    session.run("python", "-c", _INSTALLED_PROJECT_ORIGIN, env=env)
    with session.chdir("example"):
        session.run("pytest", "-n", "auto", *session.posargs, env=env)
        session.run("python", "manage.py", "check", "--fail-level", "WARNING", env=env)


@nox.session(python="3.13", venv_backend="uv")
def package(session):
    """Build the wheel and sdist and check that nothing outside the allowlist ships (scripts/check_dist.py)."""
    session.install("build")
    tmp = session.create_tmp()
    session.run("python", "-m", "build", "--outdir", f"{tmp}/dist", ".")
    session.run("python", "scripts/check_dist.py", f"{tmp}/dist")


@nox.session(python="3.13", venv_backend="uv")
def docs(session):
    """Build the documentation as Read the Docs does, failing on warnings."""
    session.install("--require-hashes", "-r", "docs/requirements.txt")
    session.run("mkdocs", "build", "--strict", "--site-dir", f"{session.create_tmp()}/site")
