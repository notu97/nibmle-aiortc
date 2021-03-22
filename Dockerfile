FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
python3-pip

RUN pip3 install --upgrade pip
RUN apt-get install ffmpeg libsm6 libxext6 -y

RUN pip3 install numpy
RUN pip3 install aiortc
RUN pip3 install opencv-python
RUN pip3 install pytest
RUN apt-get install net-tools 
RUN apt-get update
RUN apt-get upgrade
