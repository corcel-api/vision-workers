#!/bin/bash

docker build -f Dockerfile.orchestrator -t gcr.io/$PROJECT_ID/vision-workers-orchestrator:$BUILD_ID .
docker push gcr.io/$PROJECT_ID/vision-workers-orchestrator:$BUILD_ID
