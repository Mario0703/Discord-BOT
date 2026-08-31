from openai import OpenAI

from .prompts import code_review_prompt

class CodeReview:
    def __init__(self, client: OpenAI, model: str = "gpt-5.6-luna"):
        self.client = client
        self.model = model

    def do_code_review(self, language: str, code: str) -> str:
        """Review ``code`` and return the model's response as plain text."""
        response = self.client.responses.create(
            model=self.model,
            input=code_review_prompt(language, code),
        )
        return response.output_text
