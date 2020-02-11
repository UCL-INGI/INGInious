# DOCKER-VERSION 1.1.0
FROM    centos:7

ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8

LABEL org.inginious.grading.agent_version=2

# Install python, needed for scripts used in INGInious + locale support
RUN     yum clean metadata && \
        yum -y install epel-release && \
        yum -y upgrade && \
        yum -y install python python36-pip python36 zip unzip tar sed openssh-server openssl bind-utils iproute file && \
        pip3.6 install msgpack-python pyzmq jinja2 PyYAML timeout-decorator ipython mypy && \
        sed -i "s/override_install_langs=en_US.utf8/#override_install_langs=en_US.utf8/g" /etc/yum.conf && \
        yum -y reinstall glibc-common && \
        yum clean all

# Allow to run commands
ADD     . /INGInious
RUN     chmod -R 755 /INGInious/bin && \
        chmod 700 /INGInious/bin/INGInious && \
        mv /INGInious/bin/* /bin

# Install everything needed to allow INGInious' python libs to be loaded
RUN     chmod -R 644 /INGInious/inginious_container_api && \
        mkdir -p /usr/lib/python3.6/site-packages/inginious_container_api && \
        cp -R /INGInious/inginious_container_api/*.py  /usr/lib/python3.6/site-packages/inginious_container_api && \
        echo "inginious_container_api" > /usr/lib/python3.6/site-packages/inginious_container_api.pth

# This maintains backward compatibility
RUN     mkdir -p /usr/lib/python3.6/site-packages/inginious && \
        cp -R /INGInious/inginious_container_api/*.py  /usr/lib/python3.6/site-packages/inginious && \
        echo "inginious" > /usr/lib/python3.6/site-packages/inginious.pth

# Delete unneeded folders
RUN     rm -R /INGInious

# Create worker user
RUN     groupadd --gid 4242 worker && \
        useradd --uid 4242 --gid 4242 worker --home-dir /task

# Set locale params for SSH debug
RUN     echo -e "export LANG=en_US.UTF-8\nexport LANGUAGE=en_US:en\nexport LC_ALL=en_US.UTF-8\n" > /etc/profile
RUN     sed -i.bak '/^AcceptEnv/ d' /etc/ssh/sshd_config

CMD ["INGInious"]
