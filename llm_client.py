import os
from openai import OpenAI

class LLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError(
            "LLM client is not connected yet."
            "use --mode heuristic first, then replace this method with a real API call."
        )

class DeepSeekClient(LLMClient):
    def __init__(
            self, model: str = "deepseek-chat",
            api_key: str | None = None,
            base_url: str = "https://api.deepseek.com",
            max_tokens: int = 2048
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=self.max_tokens,
            stream=False,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("DeepSeek returned empty content")
        return content