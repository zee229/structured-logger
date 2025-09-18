"""
Setup script for structured-logger package.
"""
from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the version from the package
exec(open("structured_logger/_version.py").read())

setup(
    name="structured-logger",
    version=__version__,
    author="Nikita Yastreb",
    author_email="yastrebnikita723@gmail.com",
    description="A flexible structured JSON logger for Python applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zee229/structured-logger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.7",
    keywords="logging json structured railway cloud docker kubernetes",
    project_urls={
        "Bug Tracker": "https://github.com/zee229/structured-logger/issues",
        "Documentation": "https://github.com/zee229/structured-logger#readme",
        "Source Code": "https://github.com/zee229/structured-logger",
    },
)
