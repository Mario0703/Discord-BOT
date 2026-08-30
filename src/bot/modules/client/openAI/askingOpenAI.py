from openai import OpenAI


class AskOpenAI:

    def __init__(self, client=None):
        self.client = client if client is not None else OpenAI()

    def ask_openai(self, prompt: str) -> str:
        response = self.client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
        )
        return response.output_text
