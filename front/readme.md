# DEMO LABELING FOR MACHINE LEARNING


Directory Tree:
```
.
├── docker
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── Makefile
├── src
   ├── app.py
   ├── assets
   │   ├── mlex.png
   │   └── segmentation-style.css
   ├── mlex_api
   │   ├── LICENSE
   │   ├── mlex_api
   │   │   ├── database_interface.py
   │   │   ├── __init__.py
   │   │   └── job_dispatcher.py
   │   ├── README.md
   │   └── setup.py
   ├── templates.py
   ├── thumbnail.py
   └── training.py
```
This project contains several front-ends, written in dash.
thumbnail.py is a simple thumbnail display for images, allowing the user to label
the images according to some predefined class

training.py is a dash front end allowing the user to select ml models to train
on the labelled/sorted data produced by thumbnail.py. These will eventually
be integrated into one dash framework, but for now I'm developing them seperately
just for my own ease.

To use the project, it is recommended to use a docker environment. As development is
ongoing, all the requirements are directly in the dockerfile-- once I am no longer adding
dependencies as rapidly, this will be migrated to having a stand-alone requirements.txt
file.

running:
```
make build_docker
```
willl build the a local docker image for you, containing everything you need to run

running
```
make run_docker
```

will then launch a docker container where you can run the code by entering
```
python src/thumbnail.py
```
