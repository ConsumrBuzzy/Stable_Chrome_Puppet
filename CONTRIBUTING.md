# Contributing to Chrome Puppet

Thank you for considering contributing to Chrome Puppet! We appreciate your interest in making this project better.

## How to Contribute

1. **Fork** the repository on GitHub
2. **Clone** the project to your own machine
3. **Create a new branch** for your changes
4. **Commit** your changes to your branch
5. **Push** your work back up to your fork
6. Submit a **Pull Request** so we can review your changes

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

Run the test suite with:
```bash
pytest
```

## Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run all code style checks:
```bash
pre-commit run --all-files
```

## Pull Request Guidelines

- Keep PRs focused on a single feature or bug fix
- Write clear commit messages
- Update the documentation if needed
- Add tests for new features or bug fixes
- Make sure all tests pass

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any relevant error messages
- Your Python version and operating system
