"""تجريد مزود الذكاء الاصطناعي — الـ endpoints تعتمد على AIProvider فقط."""

from abc import ABC, abstractmethod
import json
import urllib.request
from app.core.config import settings


class AIProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """إتمام محادثة واحدة. يجب ألا تُمرر أي أسرار هنا — الإعدادات من البيئة فقط."""
        raise NotImplementedError


class MockProvider(AIProvider):
    """مزود تطوير: لا يتصل بأي خدمة خارجية ولا يحتاج API key."""

    NAME = "mock"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        excerpt = user_prompt[:600].replace("\n", " ").strip()
        return (
            "[وضع التطوير — MockProvider] هذه إجابة تجريبية مولّدة محليًا، "
            "مبنية على المقاطع المسترجعة أدناه. فعّل مزودًا حقيقيًا عبر AI_API_KEY "
            "للحصول على إجابات مولّدة.\n\n--- بداية السياق المسترجع ---\n"
            f"{excerpt}\n--- نهاية السياق ---"
        )


class OpenAICompatibleProvider(AIProvider):
    """مزود متوافق مع OpenAI Chat Completions عبر HTTP (urllib — بلا اعتماديات جديدة)."""

    NAME = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 800,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                # المفتاح يُرسل في الترويسة فقط ولا يُسجَّل أبدًا
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            # لا نكشف أي تفاصيل داخلية أو أسرار للمستخدم
            raise RuntimeError("AI_PROVIDER_ERROR") from exc


def get_provider() -> AIProvider:
    """اختيار المزود من الإعدادات: حقيقي فقط عند وجود مفتاح، وإلا Mock."""
    if (
        settings.AI_PROVIDER == OpenAICompatibleProvider.NAME
        and settings.AI_API_KEY
        and settings.AI_BASE_URL
    ):
        return OpenAICompatibleProvider(
            base_url=settings.AI_BASE_URL,
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL,
        )
    return MockProvider()
