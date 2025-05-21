from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chrome-puppet",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A robust and extensible Chrome browser automation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/stable_chrome_puppet",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.1",
        "beautifulsoup4>=4.12.2",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
