"""
Setup script for Chrome Puppet package.

This script handles the packaging and distribution of the Chrome Puppet package,
including its dependencies and metadata.
"""
from pathlib import Path
from setuptools import setup, find_packages

def get_version() -> str:
    """Return the package version."""
    return "0.1.0"  # Direct version string

def get_requirements(filename: str) -> list:
    """Read requirements from a requirements file."""
    requirements = []
    try:
        with open(filename, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(("#", "--")):
                    requirements.append(line)
    except FileNotFoundError:
        pass
    return requirements

# Read the README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Get dependencies
install_requires = get_requirements("requirements.txt")
dev_requires = get_requirements("requirements-dev.txt")

setup(
    name="chrome-puppet",
    version=get_version(),
    author="Robert D",
    author_email="robert.d@consumrbuzz.com",
    description="A robust and extensible Chrome browser automation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/consumrbuzzy/chrome-puppet",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.md"],
    },
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-xdist>=3.3.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-xdist>=3.3.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chrome-puppet=chrome_puppet.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
    ],
    keywords="selenium chrome automation testing webdriver",
    project_urls={
        "Bug Reports": "https://github.com/consumrbuzzy/chrome-puppet/issues",
        "Source": "https://github.com/consumrbuzzy/chrome-puppet",
    },
    license="MIT",
)
