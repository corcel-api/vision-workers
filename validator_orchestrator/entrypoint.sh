#!/bin/bash

port=${PORT:-6920}
sleep 5
source activate venv
uvicorn --lifespan on --port $port --host 0.0.0.0 app.asgi:app 

