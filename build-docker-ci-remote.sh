#!/bin/bash

docker build -f Dockerfile.orchestrator -t corcelio/cicd:$BUILD_ID .
docker push corcelio/cicd:$BUILD_ID
