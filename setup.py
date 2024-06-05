from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="mlex_file_manager",  # This is the name of the package
    version="0.0.2",  # The release version
    author="Tanny Chavez E., Zhuowen (Kevin) Zhao",  # Full name of the author
    author_email="tanchavez@lbl.gov, zzhao2@lbl.gov",
    description="",
    long_description=long_description,  # Long description read from the the readme file
    long_description_content_type="text/markdown",
    packages=find_packages(
        include=["file_manager", "file_manager.*", "file_manager.*.*"]
    ),  # List of all python modules to be installed
    license_files=("LICENSE.txt",),  # Information to filter the project on PyPi website
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Dash",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    project_urls={"Source": "https://github.com/mlexchange/mlex_file_manager.git"},
    python_requires=">=3.0",  # Minimum version requirement of the package
    # package_dir={'':'file_manager'},     # Directory of the source code of the package
    install_requires=required,  # Install other dependencies if any
)
