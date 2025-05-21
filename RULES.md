# Chrome Puppet - Project Guidelines

## Core Principles

1. **Stability First**
   - Ensure reliable browser automation
   - Implement robust error handling and recovery
   - Maintain consistent behavior across different environments

2. **Simplicity**
   - Minimal nesting in code
   - Minimal number of modules (only create new ones when absolutely necessary)
   - Clear, self-documenting code

3. **User Experience**
   - Default to visible browser (not headless) for better debugging
   - Provide clear feedback and logging
   - Make common tasks easy, complex tasks possible

4. **Configuration**
   - Sensible defaults for all settings
   - Easy configuration through code or environment variables
   - Clear documentation of all configurable options

5. **Testing**
   - All features must be tested
   - Tests should be isolated and independent
   - Include both unit and integration tests

6. **Documentation**
   - Keep documentation up-to-date
   - Include examples for common use cases
   - Document all public APIs

7. **Dependencies**
   - Minimize external dependencies
   - Pin all dependency versions
   - Document all dependencies and their purposes

8. **Error Handling**
   - Fail fast with clear error messages
   - Include context in error messages
   - Provide recovery options when possible

9. **Performance**
   - Optimize for both development speed and runtime performance
   - Profile and optimize critical paths
   - Be mindful of resource usage

10. **Security**
    - Never log sensitive information
    - Validate all inputs
    - Follow security best practices for web automation

## Development Workflow

1. **Branching**
   - `main` branch is always deployable
   - Create feature branches for new development
   - Use pull requests for code review

2. **Versioning**
   - Follow semantic versioning (MAJOR.MINOR.PATCH)
   - Update CHANGELOG.md for all releases
   - Tag releases in git

3. **Code Style**
   - Follow PEP 8 for Python code
   - Use type hints for all function signatures
   - Keep lines under 100 characters
   - Document all public methods and classes

4. **Commit Messages**
   - Use the format: `type(scope): description`
   - Types: feat, fix, docs, style, refactor, test, chore
   - Keep the first line under 50 characters
   - Include details in the body when necessary

## Project Structure

```
chrome-puppet/
├── chrome_puppet/          # Main package
│   ├── __init__.py         # Package initialization
│   ├── browser.py          # Core browser automation
│   ├── config.py           # Configuration management
│   ├── orchestrator.py     # Workflow orchestration
│   └── utils/              # Utility functions
│       ├── __init__.py
│       └── utils.py
├── tests/                  # Test cases
├── examples/               # Example scripts
├── logs/                   # Log files
├── screenshots/            # Screenshots
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-dev.txt
└── setup.py
```
