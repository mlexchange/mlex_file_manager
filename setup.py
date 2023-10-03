import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mlex_file_manager",                       # This is the name of the package
    version="0.0.1",                                # The release version
    author="Tanny Chavez E., Zhuowen (Kevin) Zhao", # Full name of the author
    author_email='tanchavez@lbl.gov, zzhao2@lbl.gov',
    description="",
    long_description=long_description,              # Long description read from the the readme file
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=['front']),   # List of all python modules to be installed
    license_files = ('LICENSE.txt',),               # Information to filter the project on PyPi website
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Dash',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Source': 'https://github.com/taxe10/mlex_file_manager.git'
    },
    python_requires='>=3.0',                        # Minimum version requirement of the package
    py_modules=["file_manager"],                    # Name of the python package
    package_dir={'':'file_manager'},                # Directory of the source code of the package
    install_requires=['dash>=2.9.3',
                      'dash[diskcache]',
                      'dash_bootstrap_components>=1.0.2',
                      'dash_daq>=0.5.0',
                      'dash_bootstrap_components==1.0.2',
                      'dash_daq==0.5.0',
                      'dash-uploader==0.6.0',
                      'requests==2.26.0',
                      'tiled[client]==0.1.0a103',
                      'dash-component-editor==0.0.7',
                      'diskcache==5.6.3',

                    ]                               # Install other dependencies if any
)