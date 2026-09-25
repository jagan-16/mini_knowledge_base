from fastapi import HTTPException
from litellm import token_counter
from services.model_loader import groq_client
from database_model import Message
from internal_models.prompt_model import Prompt
from services.groq_service import GroqService
import logging


class LLMService:

    MODEL_NAME = "openai/gpt-oss-20b"

    MODEL_CONTEXT_WINDOW = 6000

    OUTPUT_TOKEN_BUDGET = 1500

    SYSTEM_PROMPT_BUDGET = 150

    MAX_INPUT_TOKENS = (
        MODEL_CONTEXT_WINDOW
        - OUTPUT_TOKEN_BUDGET
        - SYSTEM_PROMPT_BUDGET
    )

    def __init__(self , groq_service: GroqService):
        self.logger = logging.getLogger(__name__)
        self.groq_service = groq_service

    def complete(
        self,
        prompt: Prompt,
        history: list[Message] | None = None,
        temperature: float = 0.2,
        response_format: dict | None = None,
    ) -> str:
        
       
        history = history or []

        messages = self._build_messages(
            prompt,
            history,
        )

        self._validate_token_limit(
            messages
        )

        return self.groq_service.chat_completion(
            model=self.MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=self.OUTPUT_TOKEN_BUDGET,
            response_format=response_format,
        )




            
    def _build_messages(
        self,
        prompt: Prompt,
        history: list[Message],
    ) -> list[dict]:

        messages = [

            {
                "role": "system",
                "content": prompt.system_prompt,
            }

        ]

        for message in history:

            messages.append(

                {
                    "role": message.role,
                    "content": message.content,
                }

            )

        messages.append(

            {
                "role": "user",
                "content": prompt.user_prompt,
            }

        )

        return messages

    def _validate_token_limit(
        self,
        messages: list[dict],
    ) -> None:

        input_tokens = token_counter(

            model=f"groq/{self.MODEL_NAME}",

            messages=messages,

        )

        if input_tokens > self.MAX_INPUT_TOKENS:

            raise HTTPException(
                status_code=413,
                detail=(
                    f"Input exceeds maximum allowed size "
                    f"({self.MAX_INPUT_TOKENS} tokens). "
                    f"Received {input_tokens} tokens."
                ),
            )
            
            
            