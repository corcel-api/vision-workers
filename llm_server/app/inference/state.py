import gc
import torch
import asyncio
import multiprocessing
from vllm.distributed.parallel_state import destroy_model_parallel
from app.logging import logging
from app import models
from app.inference import engines, completions, toxic
from typing import Optional

class EngineState:
    def __init__(self):
        self.llm_engine: Optional[models.LLMEngine] = None
        self.toxic_checker: Optional[models.ToxicEngine] = None
        self.model_process: Optional[multiprocessing.Process] = None

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

            await self._unload_model()

        await self._load_engine(model_to_load, revision, tokenizer_name, half_precision)

    async def _unload_model(self) -> None:
        if self.model_process is not None:
            self.model_process.terminate()
            self.model_process.join()
            logging.info(f"Terminated previous model loading process")

        if self.llm_engine is not None:
            old_model_name = self.llm_engine.model_name

            destroy_model_parallel()
            torch.distributed.destroy_process_group()

            if hasattr(self.llm_engine.model.engine, 'model_executor'):
                del self.llm_engine.model.engine.model_executor
            if hasattr(self.llm_engine.model.engine, 'tokenizer'):
                del self.llm_engine.model.engine.tokenizer
            if hasattr(self.llm_engine, 'tokenizer'):
                del self.llm_engine.tokenizer
            if hasattr(self.llm_engine, 'model'):
                del self.llm_engine.model
            del self.llm_engine
            self.llm_engine = None

            gc.collect()
            torch.cuda.empty_cache()

            if torch.cuda.is_available():
                torch.cuda.synchronize()
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

            logging.info(f"Unloaded model {old_model_name} ✅")

    async def _load_engine(
        self, model_name: str, revision: str, tokenizer_name: str, half_precision: bool
    ) -> None:
        loop = asyncio.get_event_loop()
        self.model_process = multiprocessing.Process(
            target=self._load_model_process,
            args=(model_name, revision, tokenizer_name, half_precision)
        )
        self.model_process.start()
        self.model_process.join()
        logging.info(f"Loaded new model {model_name} ✅")

    def _load_model_process(self, model_name: str, revision: str, tokenizer_name: str, half_precision: bool) -> None:
        gc.collect()
        torch.cuda.empty_cache()
        self.llm_engine = asyncio.run(engines.get_llm_engine(
            model_name, revision, tokenizer_name, half_precision
        ))

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