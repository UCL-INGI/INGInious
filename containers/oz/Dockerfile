# DOCKER-VERSION 1.1.0

FROM    INGInious/default

ADD     . /mozartRPM
RUN     rpm -i /mozartRPM/mozart2-2.0.0-3777-x86_64.rpm

RUN     echo "OZ2HOME=/opt/mozart2" >> ~/.bashrc
RUN     echo "OZHOME=/opt/mozart2" >> ~/.bashrc
RUN     echo "PATH=/opt/mozart2/bin:$""PATH" >> ~/.bashrc
