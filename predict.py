from cog import BasePredictor, Input, ConcatenateIterator
from typing import Iterator
import time

class Predictor(BasePredictor):
    def predict(
        self,
        prompt: str = Input(description="Prompt to tokenize and stream"),
    ) -> Iterator[str]:
        """Stream tokens (words) from the prompt, one at a time."""
        tokens = prompt.split()
        for token in tokens:
            time.sleep(0.2)
            yield token + " "