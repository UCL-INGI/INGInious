FROM inginious/inginious-base

COPY inginious/frontend inginious/frontend/
COPY inginious/client inginious/client/
COPY inginious-webapp .

COPY deploy/frontend.setup setup.py
RUN pip3 install .

RUN apt-get install -y git

CMD ["sh", "-c", "python3 inginious-webapp"]
