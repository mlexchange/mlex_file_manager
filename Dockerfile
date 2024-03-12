FROM python:3.9
MAINTAINER THE MLEXCHANGE TEAM

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip &&\
    pip install git+https://github.com/taxe10/mlex_file_manager

WORKDIR /app/work
ENV HOME /app/work
COPY fronty.py fronty.py

CMD ["bash"]
CMD python3 fronty.py
