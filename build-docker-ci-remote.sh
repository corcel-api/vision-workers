#!/bin/bash

docker build -f Dockerfile.orchestrator -t corcelio/cicd:orchestrator-$BUILD_ID .
docker push corcelio/cicd:orchestrator-$BUILD_ID

docker build -f Dockerfile.llm_server -t corcelio/cicd:llm-server-$BUILD_ID .
docker push corcelio/cicd:llm-server-$BUILD_ID

docker build -f Dockerfile.image_server -t corcelio/cicd:image-server-$BUILD_ID .
docker push corcelio/cicd:image-server-$BUILD_ID
