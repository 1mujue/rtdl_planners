import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, Literal
from openai import OpenAI
import anthropic
from google import genai
from google.genai import types
import re

# THE BASE CLASS!!!!!!!!!!!!!!!!!
class LLMClient(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass

# basic configurations of many LLM.
ApiType = Literal[
    "openai_compatiable",
    "anthropic_native",
    "gemini_native",
]

@dataclass(frozen=True)
class GatewayConfig:
    name: str
    api_key_env: str
    base_url: str | None = None

@dataclass(frozen=True)
class ModelConfig:
    alias: str
    gateway: str
    api_type: ApiType
    model: str
    max_tokens: int = 2048
    use_json_mode: bool = True
    extra_body: dict[str, Any] = field(default_factory=dict)

GATEWAYS: dict[str, GatewayConfig] = {
    "bailian": GatewayConfig(
        name="bailian",
        api_key_env ="DASHSCOPE_API_KEY",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
    "ofoxai_anthropic": GatewayConfig(
        name="ofoxai_anthropic",
        api_key_env="OFOXAI_API_KEY",
        base_url="https://api.ofox.ai/anthropic",
    ),
    "ofoxai_gemini": GatewayConfig(
        name="ofoxai_gemini",
        api_key_env="OFOXAI_API_KEY",
        base_url="https://api.ofox.ai/gemini",
    ),
    "ofoxai_openai": GatewayConfig(
        name="ofoxai_openai",
        api_key_env="OFOXAI_API_KEY",
        base_url="https://api.ofox.ai/v1"
    )
}

MODEL_REGISTRY: dict[str, ModelConfig] = {
    # domestic: bailian (A Li)
    "qwen": ModelConfig(
        alias="qwen",
        gateway="bailian",
        api_type="openai_compatible",
        model="qwen3.6-plus",
        max_tokens=2048,
        use_json_mode=True,
        extra_body={
            "enable_thinking": True,
        },
    ),
    "glm": ModelConfig(
        alias="glm",
        gateway="bailian",
        api_type="openai_compatible",
        model="glm-5.1",
        max_tokens=2048,
        use_json_mode=True,
    ),

    "kimi": ModelConfig(
        alias="kimi",
        gateway="bailian",
        api_type="openai_compatible",
        model="kimi-k2.5",
        max_tokens=2048,
        use_json_mode=True,
    ),

    "deepseek": ModelConfig(
        alias="deepseek",
        gateway="bailian",
        api_type="openai_compatible",
        model="deepseek-v4-flash",
        max_tokens=2048,
        use_json_mode=True,
    ),

    # foreign: OFoxAI.
    "gpt": ModelConfig(
        alias="gpt",
        gateway="ofoxai_openai",
        api_type="openai_compatible",
        model="openai/gpt-5.4",
        max_tokens=2048,
        use_json_mode=True,
    ),

    "claude": ModelConfig(
        alias="claude",
        gateway="ofoxai_anthropic",
        api_type="anthropic_native",
        model="anthropic/claude-opus-4.6",
        max_tokens=2048,
        use_json_mode=True,
    ),

    "gemini": ModelConfig(
        alias="gemini",
        gateway="ofoxai_gemini",
        api_type="gemini_native",
        model="gemini-3.1-pro-preview",
        max_tokens=2048,
        use_json_mode=True,
    ),
}

def ensure_json_instruction(system_prompt: str) -> str:
    instruction = """
Your response will be parsed directly by json.loads() in Python.

Return exactly one raw JSON object.
The first character of your response must be {.
The last character of your response must be }.

Do not use markdown.
Do not wrap the JSON in ```json or any code fence.
Do not include explanations before or after the JSON.
""".strip()

    system_prompt = system_prompt.strip()
    if not system_prompt:
        return instruction

    return system_prompt + "\n\n" + instruction

def strip_markdown_code_fence(text: str) -> str:
    text = text.strip()

    # match
    # ```json
    # {...}
    # ```
    # or：
    # ```
    # {...}
    # ```
    pattern = r"^```(?:json|JSON)?\s*(.*?)\s*```$"
    match = re.match(pattern, text, flags=re.DOTALL)

    if match:
        return match.group(1).strip()

    return text

# just extract the text between first '{' and last '}'.
def extract_json_object(text: str) -> str:
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or start >= end:
        return text

    return text[start:end + 1].strip()


def normalize_json_response(content: str) -> str:
    content = content.strip()
    content = strip_markdown_code_fence(content)
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass
    extracted = extract_json_object(content)
    json.loads(extracted)
    return extracted


def validate_and_return_content(
    *,
    content: str | None,
    source: str,
    require_json: bool,
) -> str:
    if not content:
        raise RuntimeError(f"{source} returned empty content")

    content = content.strip()

    if require_json:
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"{source} returned invalid JSON:\n{content}"
            ) from e

    return content

# We have three classes: OpenAI Compatiable, Anthropic ans Google.
class OpenAICompatibleClient(LLMClient):
    def __init__(self, gateway: GatewayConfig, model_config: ModelConfig):
        self.gateway = gateway
        self.model_config = model_config

        api_key = os.environ.get(gateway.api_key_env)
        if not api_key:
            raise ValueError(f"{gateway.api_key_env} is not set")
        
        if not gateway.base_url:
            raise ValueError(f"base_url is not set")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=gateway.base_url,
        )
    def generate(self, system_prompt, user_prompt):
        system_prompt = ensure_json_instruction(system_prompt)

        kwargs: dict[str, Any] = {
            "model": self.model_config.model,
            "messages": [
                {"role":"system", "content":system_prompt},
                {"role":"user", "content":user_prompt},
            ],
            "max_tokens": self.model_config.max_tokens,
            "stream": False,
        }

        if self.model_config.use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        if self.model_config.extra_body:
            kwargs["extra_body"] = self.model_config.extra_body

        response = self.client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content
        content = normalize_json_response(content=content)

        return validate_and_return_content(
            content=content,
            source=f"{self.gateway.name}/{self.model_config.model}",
            require_json=self.model_config.use_json_mode,
        )
    

class AnthropicNativeClient(LLMClient):
    def __init__(self, gateway: GatewayConfig, model_config: ModelConfig):
        self.gateway = gateway
        self.model_config = model_config

        api_key = os.environ.get(gateway.api_key_env)
        if not api_key:
            raise ValueError(f"{gateway.api_key_env} is not set")
        
        kwargs = {
            "api_key": api_key,
            "base_url": gateway.base_url
        }
        self.client = anthropic.Anthropic(**kwargs)

    def generate(self, system_prompt, user_prompt):
        system_prompt = ensure_json_instruction(system_prompt)
        
        message = self.client.messages.create(
            model=self.model_config.model,
            system=system_prompt,
            messages=[
                {"role":"user","content":user_prompt}
            ],
            max_tokens=self.model_config.max_tokens,
        )

        parts: list[str] = []
        for block in message.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)

        content = "".join(parts)
        content = normalize_json_response(content=content)
        
        return validate_and_return_content(
            content=content,
            source=f"{self.gateway.name}/{self.model_config.model}",
            require_json=self.model_config.use_json_mode,
        )
    

class GeminiNativeClient(LLMClient):
    def __init__(self, gateway: GatewayConfig, model_config: ModelConfig):
        self.gateway = gateway
        self.model_config = model_config

        api_key = os.environ.get(gateway.api_key_env)
        if not api_key:
            raise ValueError(f"{gateway.api_key_env} is not set")
        
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                base_url=gateway.base_url,
            ),
        )

    def generate(self, system_prompt, user_prompt):
        system_prompt = ensure_json_instruction(system_prompt)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=self.model_config.max_tokens
        )

        if self.model_config.use_json_mode:
            config.response_mime_type = "application/json"
        
        response = self.client.models.generate_content(
            model=self.model_config.model,
            contents=user_prompt,
            config=config,
        )

        content = response.text
        content = normalize_json_response(content=content)

        return validate_and_return_content(
            content=content,
            source=f"{self.gateway.name}/{self.model_config.model}",
            require_json=self.model_config.use_json_mode,
        )
    
def build_llm_client(model_alias: str) -> LLMClient:
    if model_alias not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model alias: {model_alias}. "
            f"Available models: {list(MODEL_REGISTRY.keys())}"
        )

    model_config = MODEL_REGISTRY[model_alias]
    gateway = GATEWAYS[model_config.gateway]

    if model_config.api_type == "openai_compatible":
        return OpenAICompatibleClient(gateway, model_config)

    if model_config.api_type == "anthropic_native":
        return AnthropicNativeClient(gateway, model_config)

    if model_config.api_type == "gemini_native":
        return GeminiNativeClient(gateway, model_config)

    raise ValueError(f"Unsupported api_type: {model_config.api_type}")