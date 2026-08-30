from openai import OpenAI

def ask_openai(promt: str):
    client = OpenAI()
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=promt,
    )

    return response.output_text
