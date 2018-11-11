# DOCKER-VERSION 1.1.0

#inherit from the base container, which have all the needed script to launch tasks
FROM    ingi/inginious-c-java7
LABEL org.inginious.grading.name="java7mockito"

# Add mockito and depencies
RUN cd /usr/share/java && yum install -y wget && \
	wget -O powermock.zip https://dl.bintray.com/powermock/generic/distributions/powermock-mockito2-junit-1.7.1.zip && \
	unzip powermock.zip && \
	cd powermock-mockito2-junit-1.7.1 && \
	wget http://central.maven.org/maven2/org/powermock/powermock-api-mockito-common/1.7.1/powermock-api-mockito-common-1.7.1.jar && \
cd .. && rm powermock.zip
