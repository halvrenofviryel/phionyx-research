"""
Setup script for Phionyx Core SDK
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version
version_file = Path(__file__).parent / "phionyx_core" / "__init__.py"
version = "0.2.0"
if version_file.exists():
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="phionyx-core",
    version=version,
    description="Deterministic AI Runtime Architecture — treats LLM outputs as noisy sensor measurements",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Phionyx Research",
    author_email="contact@phionyx.ai",
    url="https://github.com/halvrenofviryel/phionyx-research",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "postgres": ["asyncpg>=0.28.0"],
        "telemetry": ["opentelemetry-api>=1.20.0", "opentelemetry-sdk>=1.20.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "ruff>=0.1.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai, cognitive architecture, deterministic ai, echoism, phionyx",
    project_urls={
        "Documentation": "https://github.com/halvrenofviryel/phionyx-research#readme",
        "Source": "https://github.com/halvrenofviryel/phionyx-research",
        "arXiv Paper": "https://phionyx.ai/papers/phionyx",
        "Website": "https://phionyx.ai",
    },
)

