from openai import OpenAI


class Transcript():
    def __init__(self):
        self.client = OpenAI()
    def create_transcript(self, audio_file_path: str) -> str:
        with open(audio_file_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file
            )
        return transcript.text