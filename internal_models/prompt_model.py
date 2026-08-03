from dataclasses import dataclass


@dataclass
class Prompt:

    system_prompt: str

    user_prompt: str