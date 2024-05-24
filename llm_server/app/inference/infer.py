from app import schemas
from typing import List
from app import models
from app.inference import toxic, completions
from app.inference.state import EngineState  # Import EngineState from state.py

async def _get_last_message_content(messages: List[models.Message]):
    if len(messages) == 0:
        return None
    last_prompt = messages[-1]
    return last_prompt.content

async def infer(
    request: schemas.TextRequestModel,
    engine_state: EngineState,  # Using EngineState from state.py
    toxic_engine: models.ToxicEngine,
):
    last_message_content = await _get_last_message_content(request.messages)
    if toxic.prompt_is_toxic(toxic_engine, last_message_content):
        for o in "I am sorry, but that last request was deemed toxic, I am unable to answer.".split(
            " "
        ):
            yield o + " "
        pass
    else:
        # Send the request to the model process and wait for the response
        engine_state.parent_conn.send({'command': 'generate', 'request_info': request})
        response = engine_state.parent_conn.recv()
        yield response
