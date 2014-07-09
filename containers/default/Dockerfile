# DOCKER-VERSION 1.1.0

# We chosen centos
FROM    centos

# Update packages if it is needed
RUN     yum -y update

# Install python, needed for pythia's scripts
RUN     yum -y install python

ADD . /pythia

CMD ["python", "/pythia/pythia.py"]
