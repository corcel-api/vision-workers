import gc
import os
import torch
from huggingface_hub import scan_cache_dir
from vllm.model_executor.parallel_utils.parallel_state import destroy_model_parallel
from app.logging import logging
from app import models
from app.inference import engines, completions, toxic, patch
from typing import Optional


class EngineState:
    def __init__(self, n_device):
        self.llm_engine: Optional[models.LLMEngine] = None
        self.toxic_checker: Optional[models.ToxicEngine] = None
        self.n_device = n_device

    def load_toxic_checker(self) -> None:
        if self.toxic_checker is None:
            self.toxic_checker = toxic.get_toxic_chat_identifier()

    async def load_model_and_tokenizer(
        self,
        model_to_load: str,
        revision: str,
        tokenizer_name: str,
        half_precision: bool,
    ) -> None:
        if self.llm_engine is not None:
            if model_to_load == self.llm_engine.model_name:
                logging.info(f"Model {model_to_load} already loaded")
                return
            destroy_model_parallel()
            os.system('export MODEL='+model_to_load)
            os.system('export TOKENIZER='+tokenizer_name)
            os.system('export HALF_PRECISION='+half_precision)
            os.system('export REVISION='+revision)
            patch.stop_server_on_port([6919])
            patch.reload('/app/llm_server/entrypoint.sh')
            """
            if model_to_load == self.llm_engine.model_name:
                logging.info(f"Model {model_to_load} already loaded")
                return
            old_model_name = self.llm_engine.model_name
            try:
                destroy_model_parallel()
                logging.info(f"Unloaded model {old_model_name} ✅")
            except Exception:
                logging.debug(
                    "Tried to unload a vllm model & failed - probably wasn't a vllm model"
                )

            del self.llm_engine.model
            del self.llm_engine
            self.llm_engine = None
            """

        await self._load_engine(model_to_load, revision, tokenizer_name, half_precision, self.n_device)

    async def _load_engine(
        self, model_name: str, revision: str, tokenizer_name: str, half_precision: bool, n_device: int
    ) -> None:
        torch.cuda.empty_cache()
        gc.collect()
        try:
            self.llm_engine = await engines.get_llm_engine(
                model_name, revision, tokenizer_name, half_precision, n_device
            )
        except OSError:
            self.clean_cache_hf()
            self.llm_engine = await engines.get_llm_engine(
                model_name, revision, tokenizer_name, half_precision, n_device
            )


    # TODO: rename question & why is this needed?!
    async def grab_the_right_prompt(engine: models.LLMEngine, question: str):
        if engine.completion_method == completions.complete_img2text:
            return question
        else:
            return question
        
    def clean_cache_hf(self):
        cache_info = scan_cache_dir()
        to_clean = []
        for repo in cache_info.repos:
            to_clean += [revision.commit_hash for revision in repo.revisions]
        delete_strategy = cache_info.delete_revisions(*to_clean)
        logging.info(f"Will free {delete_strategy.expected_freed_size_str}.")
        delete_strategy.execute()

    # TODO: WHY IS THIS NEEDED?
    # async def gen_stream(self, prompt, generation_kwargs, model):
    #     loop = asyncio.get_event_loop()
    #     await loop.run_in_executor(
    #         None, lambda: self.current_model["model"].generate(**generation_kwargs)
    #     )
    #     for new_text in self.current_model["streamer"]:
    #         yield new_text
