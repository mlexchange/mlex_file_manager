from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="mlex_file_manager",
    version="0.3.0",
    author="Tanny Chavez E.",
    author_email="tanchavez@lbl.gov",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(
        include=["file_manager", "file_manager.*", "file_manager.*.*"]
    ),
    license_files=("LICENSE.txt",),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Dash",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    project_urls={"Source": "https://github.com/mlexchange/mlex_file_manager.git"},
    python_requires=">=3.10",
    install_requires=required,
)
