from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


def _load_requirements() -> list[str]:
    requirements_file = Path(__file__).parent / "requirements.txt"
    with requirements_file.open("r", encoding="utf-8") as req:
        return [line.strip() for line in req.readlines() if line.strip() and not line.startswith("#")]


setup(
    name="mlops-churn-prediction",
    version="0.1.0",
    description="Production-ready telecom churn prediction MLOps pipeline",
    author="MLOps Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=_load_requirements(),
    python_requires=">=3.11",
)
