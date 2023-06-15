# DOCKER-VERSION 1.1.0

#inherit from the base container, which have all the needed script to launch tasks
ARG   VERSION=latest
ARG   REGISTRY
FROM  ${REGISTRY}/inginious/env-base:${VERSION}

LABEL org.opencontainers.image.source=https://github.com/UCL-INGI/INGInious-containers
LABEL org.opencontainers.image.description="Default INGInious grading environment."

LABEL org.inginious.grading.name="default"
