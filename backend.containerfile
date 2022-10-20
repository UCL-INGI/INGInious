FROM ubuntu:22.04

RUN apt-get update && apt-get -y install python3 python3-pip

WORKDIR /inginious
COPY inginious/common/ inginious/common/
COPY inginious/backend/ inginious/backend/
COPY inginious-backend .

COPY backend.setup setup.py
RUN pip3 install .

CMD ["sh", "-c", "python3 inginious-backend ${AGENT} ${CLIENT}"]
