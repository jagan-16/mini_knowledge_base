from fastapi import HTTPException
from groq import (
    APIStatusError,
    
)
from litellm import token_counter
from services.model_loader import groq_client
from database_model import Message
from internal_models.prompt_model import Prompt
import logging


class LLMService:

    MODEL_NAME = "openai/gpt-oss-20b"

    MODEL_CONTEXT_WINDOW = 6000

    OUTPUT_TOKEN_BUDGET = 500

    SYSTEM_PROMPT_BUDGET = 150

    MAX_INPUT_TOKENS = (
        MODEL_CONTEXT_WINDOW
        - OUTPUT_TOKEN_BUDGET
        - SYSTEM_PROMPT_BUDGET
    )

    def __init__(self):
        self.client = groq_client

    def complete(
         self,
    prompt: Prompt,
    history: list[Message] | None = None,
    temperature: float = 0.2,
    response_format: dict | None = None,
    ) -> str:
        
        logger = logging.getLogger(__name__)
        history = history or []

        messages = self._build_messages(
            prompt,
            history,
        )

        self._validate_token_limit(
            messages
        )

        try:

            response = self.client.chat.completions.create(

                model=self.MODEL_NAME,

                messages=messages,

                temperature=temperature,

                max_tokens=self.OUTPUT_TOKEN_BUDGET,
                
                response_format=response_format, 
                
               
            )
            
            return (
                response
                .choices[0]
                .message
                .content
            )

        except APIStatusError as exc:
            
            logger.exception(
                "Groq API error. status=%s, response=%s",
                exc.status_code,
                exc,
            )

            if exc.status_code == 413:

                raise HTTPException(
                    status_code=413,
                    detail="Prompt exceeds the model context window.",
                ) from exc

            if exc.status_code == 429:

                raise HTTPException(
                    status_code=429,
                    detail="Groq rate limit exceeded. Please try again later.",
                ) from exc

            raise HTTPException(
                status_code=502,
                detail="Groq service returned an unexpected error.",
            ) from exc

        except Exception as exc:

            raise HTTPException(
                status_code=502,
                detail="Failed to generate response from the language model.",
            ) from exc

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