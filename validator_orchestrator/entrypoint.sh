#!/bin/bash

port=${PORT:-6920}

source activate venv
sleep 5
uvicorn --lifespan on --port $port --host 0.0.0.0 app.asgi:app 

