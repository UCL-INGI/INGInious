# DOCKER-VERSION 1.1.0

FROM    debian:sid

# Update packages if it is needed
RUN     apt-get update
RUN		apt-get -y upgrade

# Install python, needed for pythia's scripts
RUN     apt-get -y install python python3
RUN     apt-get -y install gcc gcc-4.4 
RUN     apt-get -y install gcc-4.4-base 
RUN     apt-get -y install cpp cpp-4.4 
RUN     apt-get -y install g++ g++-4.4 
RUN     apt-get -y install binutils libcunit1 libcunit1-dev
RUN     apt-get -y install make valgrind libc6
RUN     apt-get -y install libc-bin libgcc1 libstdc++6
RUN     apt-get -y install libmpfr4 
RUN     apt-get -y install libgmp-dev libgmp10 
RUN     apt-get -y install zlib1g 
RUN     apt-get -y install libgomp1 
RUN     apt-get -y install libc6-dev 
RUN     apt-get -y install libstdc++6-4.4-dev
RUN		apt-get -y install openjdk-6-jdk openjdk-6-jre-headless openjdk-6-jre-lib tzdata-java tzdata libc6 libc-bin libgcc1 zlib1g libnss3-1d libnspr4-0d libsqlite3-0
RUN     apt-get -y install python-pip
RUN     pip install xmltodict
RUN     ln -s /usr/lib/jvm/java-6-openjdk/bin/java /bin/java
RUN     ln -s /usr/lib/jvm/java-6-openjdk/bin/javac /bin/javac


ADD . /pythia

# Add mozart
RUN     dpkg -i /pythia/mozart2.deb

RUN     mkdir -p /usr/lib/python2.7/dist-packages/lib
RUN     cp -R /pythia/lib/*.py  /usr/lib/python2.7/dist-packages/lib
RUN     echo "lib" > /usr/lib/python2.7/dist-packages/lib.pth
RUN     mkdir -p /usr/lib/python3.4/dist-packages/lib
RUN     cp -R /pythia/lib/*.py  /usr/lib/python3.4/dist-packages/lib
RUN     echo "lib" > /usr/lib/python3.4/dist-packages/lib.pth

# Create worker user
RUN     addgroup --gid 4242 worker
RUN     useradd --uid 4242 --gid 4242 worker

CMD ["python", "/pythia/pythia.py"]
