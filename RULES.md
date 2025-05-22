# Chrome Puppet - Project Guidelines

## Core Principles

1. **Stability First**
   - Ensure reliable browser automation
   - Implement robust error handling and recovery
   - Maintain consistent behavior across different environments
   - Use virtual environments to isolate dependencies

2. **Development Environment**
   - Always use a virtual environment for development
   - Document all dependencies in `requirements.txt` and `requirements-dev.txt`
   - Keep the `.env.example` file updated with all available configuration options

3. **Simplicity**
   - Minimal nesting in code
   - Minimal number of modules (only create new ones when absolutely necessary)
   - Clear, self-documenting code

4. **User Experience**
   - Default to visible browser (not headless) for better debugging
   - Provide clear feedback and logging
   - Make common tasks easy, complex tasks possible

5. **Configuration**
   - Sensible defaults for all settings
   - Easy configuration through code or environment variables
   - Clear documentation of all configurable options

6. **Testing**
   - All features must be tested with both unit and integration tests
   - Tests should be isolated, independent, and deterministic
   - Follow the Arrange-Act-Assert pattern
   - Use descriptive test method names that describe the behavior being tested
   - Each test should verify exactly one behavior
   - Use fixtures for common test setup/teardown
   - Mark tests appropriately (e.g., @pytest.mark.browser for browser tests)
   - Include negative test cases for error conditions
   - Tests should clean up after themselves
   - Browser tests should be marked with @pytest.mark.browser
   - Driver tests should be marked with @pytest.mark.driver
   - Keep tests focused and fast (avoid unnecessary browser launches)

7. **Test Structure**
   - Unit tests should be in the `tests/unit` directory
   - Integration tests should be in the `tests/integration` directory
   - Browser tests should be in the `tests/browser` directory
   - Test files should be named `test_*.py` or `*_test.py`
   - Test classes should be named `Test*`
   - Test methods should be named `test_*`
   - Use fixtures for test data and common setup
   - Keep test data in the `tests/test_data` directory
   - Use pytest markers to categorize tests
   - Document test dependencies and requirements

9. **Documentation**
   - Keep documentation up-to-date
   - Include examples for common use cases
   - Document all public APIs

8. **Dependencies**
   - Minimize external dependencies
   - Pin all dependency versions
   - Document all dependencies and their purposes

9. **Error Handling**
   - Fail fast with clear error messages
   - Include context in error messages
   - Provide recovery options when possible

10. **Performance**
   - Optimize for both development speed and runtime performance
   - Profile and optimize critical paths
   - Be mindful of resource usage

11. **Security**
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
