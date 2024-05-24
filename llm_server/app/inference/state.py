import gc
import torch
import asyncio
import multiprocessing
from multiprocessing.context import SpawnContext
from vllm.distributed.parallel_state import destroy_model_parallel
from app.logging import logging
from app import models
from app.inference import engines, completions, toxic
from typing import Optional

class EngineState:
    def __init__(self):
        self.current_model: Optional[str] = None
        self.llm_engine_loaded: bool = False
        self.toxic_checker: Optional[models.ToxicEngine] = None
        self.model_process: Optional[multiprocessing.Process] = None
        self.parent_conn, self.child_conn = multiprocessing.Pipe()
        self.model_ready = multiprocessing.Event()

        # Set the multiprocessing start method to 'spawn'
        ctx = multiprocessing.get_context('spawn')
        self.parent_conn, self.child_conn = ctx.Pipe()
        self.model_ready = ctx.Event()

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
        if self.llm_engine_loaded and not force_reload and self.current_model == model_to_load:
            logging.info(f"Model {model_to_load} already loaded")
            return

        await self._unload_model()

        await self._load_engine(model_to_load, revision, tokenizer_name, half_precision)

    async def _unload_model(self) -> None:
        if self.model_process is not None:
            self.parent_conn.send({'command': 'terminate'})
            self.model_process.join()
            logging.info(f"Terminated previous model loading process")

        self.llm_engine_loaded = False
        self.current_model = None
        gc.collect()
        torch.cuda.empty_cache()

        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        logging.info(f"Unloaded model")

    async def _load_engine(
        self, model_name: str, revision: str, tokenizer_name: str, half_precision: bool
    ) -> None:
        self.model_ready.clear()
        ctx = multiprocessing.get_context('spawn')
        self.model_process = ctx.Process(
            target=self._load_model_process,
            args=(model_name, revision, tokenizer_name, half_precision, self.child_conn, self.model_ready)
        )
        self.model_process.start()

        # Wait until the model is loaded
        self.model_ready.wait()
        self.llm_engine_loaded = True
        self.current_model = model_name
        logging.info(f"Loaded new model {model_name} ✅")

    def _load_model_process(self, model_name: str, revision: str, tokenizer_name: str, half_precision: bool, conn: multiprocessing.connection.Connection, model_ready: multiprocessing.Event) -> None:
        async def load_and_listen():
            gc.collect()
            torch.cuda.empty_cache()
            llm_engine = await engines.get_llm_engine(
                model_name, revision, tokenizer_name, half_precision
            )
            model_ready.set()  # Signal that the model is loaded

            while True:
                message = conn.recv()
                if message['command'] == 'terminate':
                    break
                elif message['command'] == 'generate':
                    request_info = message['request_info']
                    response = await self._generate(llm_engine, request_info)
                    conn.send(response)

        asyncio.run(load_and_listen())

    async def _generate(self, llm_engine: models.LLMEngine, request_info: models.RequestInfo) -> str:
        response = ""
        async for chunk in completions.complete_vllm(llm_engine, request_info):
            response += chunk
        return response

    async def generate_text(self, request_info: models.RequestInfo) -> str:
        self.parent_conn.send({'command': 'generate', 'request_info': request_info})
        return self.parent_conn.recv()

    # TODO: rename question & why is this needed?!
    async def grab_the_right_prompt(engine: models.LLMEngine, question: str):
        if engine.completion_method == completions.complete_img2text:
            return question
        else:
            return question
