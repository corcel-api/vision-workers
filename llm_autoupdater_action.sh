#!/bin/bash

# THIS FILE CONTAINS ACTIONS TO BE PERFORMED FOR LLM SERVER AT GIT UPDATE

# THIS FILE CONTAINS THE STEPS NEEDED TO AUTOMATICALLY UPDATE THE REPO ON A TAG CHANGE
# THIS FILE ITSELF MAY CHANGE FROM UPDATE TO UPDATE, SO WE CAN DYNAMICALLY FIX ANY ISSUES

# SOME STEPS ARE COMMENTED OUT IN THIS UPDATE AS THEY ARE NOT NEEDED

echo "Just some changes"
echo "Just some changes"
echo "Just some changes"
echo "Just some changes"

pm2 start ecosystem_llm.config.js --only entrypoint
