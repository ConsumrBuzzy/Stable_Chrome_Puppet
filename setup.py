from setuptools import setup, find_packages
import pathlib

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = [
        line.strip() 
        for line in f 
        if line.strip() and not line.startswith(("#", "--"))
    ]

# Read the README
this_directory = pathlib.Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="chrome-puppet",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A robust and extensible Chrome browser automation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/chrome-puppet",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_dir={
        "chrome_puppet": "core"
    },
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],
    },
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
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
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
