from typing import List
from app import models


def create_llm_prompt(messages: List[models.Message]):
    """
    Function to create a structured prompt from a list of message dictionaries.

    Parameters:
    - messages (list): A list of dictionaries, each containing 'role' and 'content' keys.

    Returns:
    - str: A structured prompt ready for use with an LLM.
    """
    prompt = ""
    for message in messages:
        role = message.role
        content = message.content
        prompt += f"{role.value}: {content}\n"
    # TODO: Check if we need the last \n
    return prompt


def determine_needs_await(cuda_version: str) -> bool:
    return float(cuda_version) < 12.1

