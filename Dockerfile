FROM python:3.9
MAINTAINER THE MLEXCHANGE TEAM

COPY requirements.txt requirements.txt
COPY setup.py setup.py
COPY file_manager file_manager
COPY README.md README.md

RUN pip install --upgrade pip &&\
    pip install .

WORKDIR /app/work
ENV HOME /app/work
COPY fronty.py fronty.py
COPY plot_utils.py plot_utils.py
COPY assets assets

CMD ["bash"]
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--reload", "fronty:server"]
