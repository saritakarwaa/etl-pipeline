import json
from pathlib import Path


class CheckpointManager:

    def __init__(
        self,
        checkpoint_file: str
    ):

        self.file_path = Path(
            checkpoint_file
        )

    def save(
        self,
        data: dict
    ) -> None:

        with open(
            self.file_path,
            "w"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    def load(
        self
    ) -> dict:

        if not self.file_path.exists():

            return {}

        with open(
            self.file_path,
            "r"
        ) as file:

            return json.load(
                file
            )