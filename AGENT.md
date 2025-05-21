# Agent Onboarding Guide

Welcome to the Chrome Puppet project! This guide will help you quickly understand the project structure, conventions, and how to work with the codebase.

## Project Overview

Chrome Puppet is a robust and extensible Chrome browser automation tool built with Selenium and Python. It's designed to be a parent project for future browser automation projects, providing a solid foundation with common functionality.

## Key Features

- 🚀 Self-contained Chrome and ChromeDriver management
- 🔄 Automatic browser version detection and compatibility handling
- 🧩 Extensible base class for different website platforms
- 🛡️ Built-in error handling and recovery
- 🖥️ Support for both headless and headed modes
- 🔍 Integration with BeautifulSoup for HTML parsing
- 📸 Screenshot capture with timestamps

## Project Structure

```
chrome-puppet/
├── .github/                 # GitHub workflows and issue templates
├── core/                    # Core browser automation code
│   ├── __init__.py
│   ├── browser/            # Browser implementation
│   │   ├── __init__.py
│   │   ├── base.py         # Base browser interface
│   │   ├── chrome.py       # Chrome implementation
│   │   ├── element.py      # Element handling
│   │   ├── exceptions.py   # Custom exceptions
│   │   ├── navigation.py   # Navigation utilities
│   │   └── screenshot.py   # Screenshot functionality
│   ├── config.py           # Configuration management
│   └── orchestrator.py     # High-level browser orchestration
├── examples/               # Example scripts
├── screenshots/            # Directory for saved screenshots
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── base_test.py        # Base test class
│   ├── test_basic.py       # Basic functionality tests
│   ├── test_browser_init.py # Browser initialization tests
│   └── test_navigation.py  # Navigation tests
├── .env.example           # Example environment variables
├── .gitignore
├── CHANGELOG.md           # Project changelog
├── LICENSE
├── main.py                # Command-line interface
├── README.md              # Project documentation
├── requirements-dev.txt   # Development dependencies
├── requirements.txt       # Runtime dependencies
└── setup.py               # Package installation script
```

## Getting Started

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/consumrbuzzy/chrome-puppet.git
   cd chrome-puppet
   ```

2. Set up the environment (Windows):
   ```powershell
   .\setup_env.ps1
   ```

   Or manually:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints for all function signatures
- Keep lines under 100 characters
- Document all public methods and classes

### Testing

Run tests:
```bash
pytest tests/ -v
```

### Documentation

- Keep docstrings up to date
- Update README.md for major changes
- Add examples for new features
- Document all configuration options

## Common Tasks

### Adding a New Feature

1. Create a feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```

2. Implement your changes
3. Add tests
4. Update documentation
5. Submit a pull request

### Debugging

- Check logs in `logs/` directory
- Enable debug logging by setting `LOG_LEVEL=DEBUG` in `.env`
- Use the `--debug` flag when running scripts

## Best Practices

1. **Error Handling**: Always handle potential errors and provide meaningful messages
2. **Resource Management**: Use context managers (`with` statements) for browser sessions
3. **Configuration**: Use environment variables for sensitive or environment-specific settings
4. **Testing**: Write tests for new functionality
5. **Documentation**: Keep documentation up to date

## Troubleshooting

### ChromeDriver Issues

If you encounter ChromeDriver version mismatches:
1. Check your Chrome version
2. Ensure the correct ChromeDriver version is installed
3. Update Chrome or ChromeDriver if needed

### Common Errors

- **Browser not found**: Ensure Chrome/Chromium is installed and in PATH
- **Element not found**: Add explicit waits or increase timeout
- **Stale element**: Re-find the element if the page changes

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/consumrbuzzy/chrome-puppet/issues) page.
