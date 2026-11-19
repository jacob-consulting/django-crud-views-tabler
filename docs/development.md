# Development

## Layout of the repository

| Path | What |
|---|---|
| `src/crud_views_tabler/`, `src/django_tabler/` | the two packages of the distribution |
| `tests/crispy_tabler/`, `tests/crud_views_tabler/`, `tests/django_tabler/` | package tests, each with its own settings |
| `example/` | the Acme Roasters demo project and its tests |
| `docs/` | this documentation (Read the Docs) |
| `dev/` | maintainer notes: the [findings log](https://github.com/jacob-consulting/django-crud-views-tabler/blob/main/dev/crud_views_upstream_findings_roastery.md) of django-crud-views gaps and the questions to upstream |
| `superpowers/` | design specs and implementation plans |
| `scripts/` | `vendor_templates.py` (crispy pack), `check_dist.py`, `check_release_floor.py` |

## Local setup

The theme tracks django-crud-views features that may not be released yet. Locally, django-crud-views and
django-crud-views-extensions are installed from sibling checkouts (`[tool.uv.sources]` in `pyproject.toml`):

```shell
git clone https://github.com/jacob-consulting/django-crud-views.git
git clone https://github.com/jacob-consulting/django-crud-views-extensions.git
git clone https://github.com/jacob-consulting/django-crud-views-tabler.git
cd django-crud-views-tabler
task up      # uv sync --extra examples --extra test --extra dev, migrate, superuser admin/admin, seed, runserver
```

Without [Task](https://taskfile.dev):

```shell
uv sync --extra examples --extra test --extra dev
uv run python example/manage.py migrate
uv run python example/manage.py cv_manage_group
uv run python example/manage.py seed_demo            # accounts alex, sam, kim (password demo)
uv run python example/manage.py seed_demo_showcase   # not idempotent: run once
uv run python example/manage.py runserver
```

## Tests

```shell
task test          # every suite against the sibling checkouts, plus the system check
task test:matrix   # the nox matrix, as CI runs it
```

`task test` runs, with `uv run`:

```shell
pytest -n auto                                                        # tests/crispy_tabler
pytest -n auto tests/crud_views_tabler --ds tests.crud_views_tabler.settings
pytest -n auto tests/django_tabler --ds tests.django_tabler.settings
cd example && pytest -n auto                                         # the demo apps
python example/manage.py check --fail-level WARNING
```

The nox sessions (`noxfile.py`) build and install the distribution, so a packaging mistake fails the tests:

- `tests-<python>(django='<version>')`: the three package suites, with coverage;
- `examples-<python>(django='<version>')`: the demo's tests and its system check;
- `package`: builds wheel and sdist and runs `scripts/check_dist.py`;
- `docs`: `mkdocs build --strict`.

The matrix is Python 3.12–3.15 × Django 5.2, 6.1. Until django-crud-views 1.0.0rc1 is on PyPI, nox (and the
Render demo) install django-crud-views from its GitHub `main` (`CRUD_VIEWS` in `noxfile.py`,
`requirements/demo.txt`).

Lint with ruff (`pre-commit install` runs it on commit):

```shell
uv run ruff format . && uv run ruff check .
```

## The crispy pack

`scripts/vendor_templates.py` copies the templates from the installed crispy-bootstrap5 into
`src/django_tabler/templates/crispy_tabler/`, rewriting `bootstrap5/` includes. Six templates are hand-edited and are
not overwritten without `--force`. `django_tabler/crispy/vendored.py:CRISPY_BOOTSTRAP5_VERSION` must equal the
`crispy-bootstrap5` pin of the `test` extra; `tests/crispy_tabler/test_pack_parity.py` fails otherwise.

## Releasing

1. Once django-crud-views 1.0.0rc1 is on PyPI: remove `CRUD_VIEWS` from `noxfile.py` and the git line from
   `requirements/demo.txt`; raise the floor in `pyproject.toml` to `django-crud-views (>=1.0.0rc1)`; flip
   `test_repository_is_not_releasable_yet` in `tests/django_tabler/test_release_floor.py`.
2. Update `CHANGELOG.md`.
3. The first release is the version already in the files: `git tag v0.1.0`. Later ones:
   `uv run bump-my-version bump patch` (or `minor`/`major`), which updates `pyproject.toml`, both `__init__.py`,
   `README.md` and `docs/index.md`, commits and tags `v<version>`.
4. `git push --follow-tags`. The tag runs `publish.yml` (release floor check, tests, docs, lint, PyPI) and `demo.yml`
   (deploys that commit to Render).

`publish.yml` refuses to publish while the django-crud-views floor is below 1.0.0rc1
(`scripts/check_release_floor.py`).

## One-time account setup

- **GitHub**: repository `jacob-consulting/django-crud-views-tabler`, public; environment `pypi`; secrets
  `CODECOV_TOKEN`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`; variable `DEMO_URL` (the Render URL).
- **PyPI**: a trusted publisher for project `django-crud-views-tabler`: owner `jacob-consulting`, repository
  `django-crud-views-tabler`, workflow `publish.yml`, environment `pypi`.
- **Read the Docs**: import the repository; `.readthedocs.yaml` configures the build.
- **Codecov**: add the repository and copy its upload token into `CODECOV_TOKEN`.
- **Render**: New → Blueprint from the repository (`render.yaml`); copy the service id into `RENDER_SERVICE_ID` and
  an API key into `RENDER_API_KEY`. Deploys come from `demo.yml` only (`autoDeploy: false`); run it by hand
  (Actions → demo → Run workflow on `main`) to deploy before the first release.
