import gc
import os
from time import sleep

import torch
from vllm.distributed.parallel_state import destroy_model_parallel
from app.logging import logging
from app import models
from app.inference import engines, completions, toxic
from typing import Optional
import subprocess


def clear_gpu_memory():
    logging.info('Clearing cuda objects from gc')
    for obj in gc.get_objects():
        try:
            if torch.is_tensor(obj):
                if obj.is_cuda:
                    del obj
            elif hasattr(obj, 'data') and torch.is_tensor(obj.data):
                if obj.data.is_cuda:
                    del obj
        except Exception as e:
            print(f"Error while clearing object: {e}")
    gc.collect()    
    torch.cuda.empty_cache()

def restart_nvidia_driver():
    commands = [
        "sudo rmmod nvidia_uvm",
        "sudo rmmod nvidia",
        "sudo modprobe nvidia",
        "sudo modprobe nvidia_uvm"
    ]
    logging.info('Restarting cuda drivers to make sure GPU memory is freed')
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())
            if result.stderr:
                print(result.stderr.decode())
        except subprocess.CalledProcessError as e:
            print(f"Error running command '{cmd}': {e.stderr.decode()}")

class EngineState:
    def __init__(self):
        self.llm_engine: Optional[models.LLMEngine] = None
        self.toxic_checker: Optional[models.ToxicEngine] = None

    def load_toxic_checker(self) -> None:
        if self.toxic_checker is None:
            self.toxic_checker = toxic.get_toxic_chat_identifier()

    async def load_model_and_tokenizer(
        self,
        model_to_load: str,
        revision: str,
        tokenizer_name: str,
        half_precision: bool,
        force_reload: bool,
    ) -> None:
        if self.llm_engine is not None:
            if model_to_load == self.llm_engine.model_name and not force_reload:
                logging.info(f"Model {model_to_load} already loaded")
                return
            old_model_name = self.llm_engine.model_name
            # unloading & clearing cache
            destroy_model_parallel()
            torch.distributed.destroy_process_group()
            del self.llm_engine.model.engine.model_executor 
            del self.llm_engine.model.engine.tokenizer
            del self.llm_engine.tokenizer
            del self.llm_engine.model
            del self.llm_engine
            self.llm_engine = None
            clear_gpu_memory()
            gc.collect()
            restart_nvidia_driver()
            logging.info(f"Unloaded model {old_model_name} ✅")

        await self._load_engine(model_to_load, revision, tokenizer_name, half_precision)

    async def _load_engine(
        self, model_name: str, revision: str, tokenizer_name: str, half_precision: bool
    ) -> None:
        torch.cuda.empty_cache()
        gc.collect()
        self.llm_engine = await engines.get_llm_engine(
            model_name, revision, tokenizer_name, half_precision
        )

    # TODO: rename question & why is this needed?!
    async def grab_the_right_prompt(engine: models.LLMEngine, question: str):
        if engine.completion_method == completions.complete_img2text:
            return question
        else:
            return question

    # TODO: WHY IS THIS NEEDED?
    # async def gen_stream(self, prompt, generation_kwargs, model):
    #     loop = asyncio.get_event_loop()
    #     await loop.run_in_executor(
    #         None, lambda: self.current_model["model"].generate(**generation_kwargs)
    #     )
    #     for new_text in self.current_model["streamer"]:
    #         yield new_text
