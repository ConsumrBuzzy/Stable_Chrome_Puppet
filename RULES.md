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
   - Use the provided `setup_env.ps1` script for consistent environment setup
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
   - All features must be tested
   - Tests should be isolated and independent
   - Include both unit and integration tests

7. **Documentation**
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
