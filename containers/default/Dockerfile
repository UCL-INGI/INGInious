# DOCKER-VERSION 1.1.0

# We chose centos
FROM    centos

# Install python, needed for pythia's scripts
RUN     yum -y install python

ADD     . /INGInious

# Allow to run commands
RUN     mv /INGInious/bin/* /bin

# Install everything needed to allow INGInious' python libs to be loaded
RUN     mkdir -p /usr/lib/python2.7/site-packages/inginious
RUN     cp -R /INGInious/inginious/*.py  /usr/lib/python2.7/site-packages/inginious
RUN     echo "inginious" > /usr/lib/python2.7/site-packages/inginious.pth

# Delete unneeded folders
RUN     rm -R /INGInious

# Create worker user
RUN     groupadd --gid 4242 worker
RUN     useradd --uid 4242 --gid 4242 worker

CMD ["INGInious"]
