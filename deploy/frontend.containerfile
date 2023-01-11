FROM inginious/inginious-base

COPY inginious/frontend inginious/frontend/
COPY inginious/client inginious/client/
COPY inginious-webapp .

RUN dnf install -y git gcc python39-devel

COPY deploy/frontend.setup setup.py
RUN pip3 install .

COPY deploy/db_setup.py /tmp/db_setup.py

CMD ["sh", "-c", "python3 /tmp/db_setup.py; python3 inginious-webapp"]
