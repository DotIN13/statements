import os
import random
import json
import time

import httpx

from lib.exceptions import (
    BadResponseException,
    CensoredResponseException,
    TooManyRequestsException
)

HEADERS = {"Content-Type": "application/json", "Authorization": ""}

# Default mapping of platform names to their API endpoints.
ENDPOINT_PROXIES = {
    "openai": ["https://api.openai.com"],
    "deepseek": ["https://api.deepseek.com"],
    "dashscope": ["https://dashscope.aliyuncs.com/compatible-mode"],
    "local": ["http://localhost:8000"],  # Local endpoint for VLLM
}


def debug_context(completion, res):
    context = f"Response Code: {completion.status_code if completion else 'None'}\n"
    context += f"Raw Response: {completion.text if completion else 'None'}\n"
    context += f"Response: {res if res else 'None'}"
    return context


class ChatModel():
    def __init__(self, name, proxies, api_key=None, **args):
        if not isinstance(proxies, list) or len(proxies) == 0:
            raise ValueError(
                "Cannot initialize ChatModel with empty proxies list.")

        self.headers = HEADERS.copy()
        self.headers["Authorization"] = f"Bearer {api_key}"

        self.name = name  # Model name used when sending requests
        self.proxies = proxies
        self.args = args or {}

    def __repr__(self):
        return f"ChatModel({self.name})"


class OpenAIChatModel(ChatModel):
    def __init__(self, name, proxies=None, api_key=None, **args):
        proxies = proxies or ENDPOINT_PROXIES["openai"]
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(name, proxies, api_key, **args)


class DeepSeekChatModel(ChatModel):
    def __init__(self, name, proxies=None, api_key=None, **args):
        proxies = proxies or ENDPOINT_PROXIES["deepseek"]
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        super().__init__(name, proxies, api_key, **args)


class LocalChatModel(ChatModel):
    def __init__(self, name, proxies=None, api_key=None, **args):
        proxies = proxies or ENDPOINT_PROXIES["local"]
        super().__init__(name, proxies, api_key, **args)


class ChatClient():
    def __init__(self, timeout=120.0):
        self.backoff = 0.0
        client_timeout = httpx.Timeout(timeout, connect=10.0)
        self.client = httpx.AsyncClient(http2=True, timeout=client_timeout)

    def set_backoff(self, backoff):
        self.backoff = backoff
        self.backoff = max(0.0, self.backoff)
        self.backoff = min(32.0, self.backoff)

    async def chat_completions(
        self,
        message=None,
        context=None,
        model=None,
        debug=False,
    ):
        completion = None
        res = None

        try:
            if not isinstance(model, ChatModel):
                raise ValueError("Chat Model must be specified.")

            if self.backoff > 1.0:
                print(f"Calling LLM with backoff: {self.backoff} seconds.")
            time.sleep(self.backoff + random.random() * 0.3)

            messages = context or []
            if message:  # If a string prompt message is provided by the user
                messages.append({"role": "user", "content": message})

            if not messages:
                raise ValueError("No prompt messages provided")

            completion = await self.client.post(
                f"{random.choice(model.proxies)}/v1/chat/completions",
                json={
                    "model": model.name,
                    "messages": messages,
                    **model.args,  # Additional model-specific arguments
                },
                headers=model.headers,
            )

            if completion.status_code == 429:
                self.set_backoff(self.backoff * 2.0 + 1.0)
                raise TooManyRequestsException(
                    "API rate limit exceeded. Retrying after backoff.")

            if completion.status_code != 200:
                res = completion.json()

                if res.get("error", {}).get("code") == "RequestTimeOut":
                    self.set_backoff(self.backoff * 2.0 + 1.0)
                    raise TooManyRequestsException(
                        "API rate limit exceeded. Retrying after backoff.")

                if res.get("error", {}).get("message") == "Content Exists Risk":
                    raise CensoredResponseException(
                        "API response content is censored.")

                raise BadResponseException("Unexpected status code.")

            res = completion.json()

            if debug == "usage":
                print(
                    f"[DEBUG] Usage: {res.get('usage', 'No usage information found.')}")

            result_content = res.get("choices", [{}])[0] \
                .get("message", {}) \
                .get("content", None)

            if not result_content:
                raise BadResponseException(
                    "Missing or malformed content in response.")

            self.set_backoff(self.backoff / 2.0 - 1.0)
            return res

        except TooManyRequestsException as err:
            raise BadResponseException(
                f"TooManyRequestsException: {str(err)} | Current backoff: {self.backoff} seconds."
            ) from err
        except httpx.RequestError as err:
            raise BadResponseException(
                f"HTTPX RequestError: {str(err)} | Possible network issues or misconfiguration."
            ) from err
        except json.JSONDecodeError as err:
            raise BadResponseException(
                f"JSON Decode Error: {str(err)} | {debug_context(completion, res)}"
            ) from err
        except ValueError as err:
            raise BadResponseException(
                f"ValueError: {str(err)} | {debug_context(completion, res)}"
            ) from err
        except KeyError as err:
            raise BadResponseException(
                f"KeyError: {str(err)} | {debug_context(completion, res)}"
            ) from err
        except CensoredResponseException as err:
            raise CensoredResponseException(
                f"CensoredResponseException: {str(err)} | {debug_context(completion, res)}"
            ) from err
        except Exception as err:
            raise BadResponseException(
                f"Unexpected Error: {str(err)} | {debug_context(completion, res)}"
            ) from err

    async def close(self):
        """Close httpx client"""
        await self.client.aclose()
