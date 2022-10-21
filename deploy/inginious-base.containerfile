FROM ubuntu:22.04

RUN apt-get update && apt-get -y install python3 python3-pip

WORKDIR /inginious
COPY inginious/common/ inginious/common/
COPY inginious/__init__.py inginious/
