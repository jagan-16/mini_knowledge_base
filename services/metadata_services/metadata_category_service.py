import json
from pathlib import Path


class MetadataConfigService:

    def __init__(self):
        self.categories_path = (
            Path(__file__).resolve().parents[2]
            / "metadata_categories.txt"
        )

    def get_categories(
        self,
    ) -> dict[str, list[str]]:

        try:

            content = self.categories_path.read_text(
                encoding="utf-8"
            )

            return json.loads(content)

        except FileNotFoundError as exc:

            raise RuntimeError(
                "Metadata categories configuration file not found."
            ) from exc

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Metadata categories configuration contains invalid JSON."
            ) from exc