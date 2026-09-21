import logging
from fastapi import HTTPException
from groq import APIStatusError

from services.model_loader import groq_client


class GroqService:

    def __init__(self):

        self.client = groq_client
        self.logger = logging.getLogger(__name__)

    def chat_completion(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int | None = None,
        max_completion_tokens: int | None = None,
        response_format: dict | None = None,
        top_p: float | None = None,
        reasoning_effort: str | None = None,
        reasoning_format: str | None = None,
    ) -> str:

        try:

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                max_completion_tokens=max_completion_tokens,
                response_format=response_format,
                top_p=top_p,
                reasoning_effort=reasoning_effort,
                reasoning_format=reasoning_format,
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if not content:

                raise HTTPException(
                    status_code=502,
                    detail="Groq returned an empty response.",
                )

            return content

        except APIStatusError as exc:

            self.logger.exception(
                "Groq API error. status=%s, response=%s",
                exc.status_code,
                exc,
            )

            if exc.status_code == 413:

                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Groq request exceeds "
                        "the model context window."
                    ),
                ) from exc

            if exc.status_code == 429:

                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Groq rate limit exceeded. "
                        "Please try again later."
                    ),
                ) from exc

            raise

        except HTTPException:
            raise

        except Exception:

            self.logger.exception(
                "Unexpected error during Groq completion."
            )

            raise