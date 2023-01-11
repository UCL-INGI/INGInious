FROM rockylinux:8

RUN dnf update -y && dnf install -y python39 python39-pip
RUN pip3 install importlib-metadata

WORKDIR /inginious
COPY inginious/common/ inginious/common/
COPY inginious/__init__.py inginious/
