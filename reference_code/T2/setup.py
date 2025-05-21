from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dnc_genie",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automation tool for managing Zoom Do Not Call (DNC) lists",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dnc-genie",
    packages=find_packages(exclude=["tests", "tests.*", "reference", "reference.*", "backup_*"]),
    include_package_data=True,
    install_requires=[
        'selenium>=4.0.0,<5.0.0',
        'python-dotenv>=0.21.0,<2.0.0',
        'colorama>=0.4.4,<1.0.0',
        'pydantic>=2.0.0,<3.0.0',
        'pydantic-settings>=2.0.0,<3.0.0',
    ],
    python_requires='>=3.8',
    extras_require={
        'dev': [
            'pytest>=7.0.0,<8.0.0',
            'pytest-cov>=3.0.0,<4.0.0',
            'black>=22.0.0,<23.0.0',
            'flake8>=5.0.0,<6.0.0',
            'mypy>=0.981,<1.0',
            'types-python-dotenv>=0.19.0,<1.0.0',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'dnc-genie=main:main',
        ],
    },
)
