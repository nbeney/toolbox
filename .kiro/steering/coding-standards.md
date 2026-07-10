# Coding Standards

## Shell / Bash

- Always use `${variable}` instead of `$variable` for variable expansions.
- Always quote variable expansions: `"${variable}"` unless word splitting is explicitly needed.
- Command-line options should have both a short form (e.g. `-v`) and a long form (e.g. `--verbose`) where possible.
- Continuation lines (after `\`) must be indented with 4 spaces.

## Python

- Always format code with `uvx ruff format`.
- Always lint code with `uvx ruff check --fix`.
- Use `uv` to manage Python dependencies instead of `pip install` / etc.
- Use `uvx` to run Python tools instead of `pipx` / etc.
- Use [pytest](https://docs.pytest.org/) for tests.
- Use [syrupy](https://github.com/syrupy-project/syrupy) for characterization (snapshot) tests.
- Use [Playwright](https://playwright.dev/python/) for web frontend tests.
- Use [Typer](https://typer.tiangolo.com/) for CLI argument parsing.
- Use [Rich](https://rich.readthedocs.io/) for pretty terminal output (tables, colours, progress bars, etc.).
- Use [Dominate](https://github.com/Knio/dominate) for HTML generation.).
- When creating a new script with a `if __name__ == "__main__"`, add a `#!/usr/local/bin/uv run` shebang and make it executable.
- When creating CLI options/arguments, please define module-level variables using typer.Option(...) or typer.Argument() and then used by name in the function signature. See db-tool/src/app.py for an example.
