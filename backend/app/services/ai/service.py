"""خدمة الذكاء الاصطناعي التعليمية — تبني الـ prompts وتستدعي المزود."""

import json

from app.services.ai.provider import get_provider, MockProvider


SYSTEM_PROMPT_AR = """أنت مساعد تعليمي عربي ضمن منصة «مراجعي الذكي».

القواعد الصارمة:
1. أجب اعتمادًا على «السياق المسترجع من دروس المنصة» عندما يكون السؤال متعلقًا بالدرس.
2. لا تدّعِ أبدًا أن معلومة موجودة في الدرس إذا لم تكن في السياق المعطى لك.
3. لا تخترع مصادر أو أسماء كتب أو أرقام صفحات أو اقتباسات.
4. إذا كان السياق غير كافٍ للإجابة، قل بوضوح أن محتوى المنصة المتاح لا يكفي للإجابة عن هذا السؤال.
5. اشرح للطالب بأسلوب واضح ومبسط بدل الإجابات الغامضة، واستخدم العربية الفصيحة المبسطة.
6. إذا كان السؤال خارج محتوى الدرس، وضّح ذلك صراحة.
7. يجوز تقديم شرح عام من معرفتك العامة فقط إذا طُلب ذلك صراحة، مع التمييز الواضح بينه وبين محتوى الدرس (ضع عنوان «شرح عام — ليس من محتوى الدرس»).
8. احترم مستوى الطالب الدراسي عندما يُذكر لك.
"""

INSUFFICIENT_CONTENT_MESSAGE = (
    "محتوى المنصة المتاح حاليًا لا يكفي للإجابة عن هذا السؤال. "
    "جرّب إعادة صياغة السؤال، أو اطلب من المشرف إضافة محتوى الدرس ذي الصلة."
)


class AIService:
    def __init__(self):
        self.provider = get_provider()

    @property
    def is_mock(self) -> bool:
        return isinstance(self.provider, MockProvider)

    def build_user_prompt(
        self,
        question: str,
        context_blocks: list[str],
        action: str = "ask",
        student_level: str | None = None,
    ) -> str:
        parts = []
        if student_level:
            parts.append(f"المستوى الدراسي للطالب: {student_level}.")
        if context_blocks:
            parts.append("السياق المسترجع من دروس المنصة:")
            for i, block in enumerate(context_blocks, 1):
                parts.append(f"[مقطع {i}]\n{block}")
        if action == "explain":
            parts.append(
                "المطلوب: اشرح الدرس أعلاه شرحًا تعليميًا منظمًا بالاعتماد على السياق فقط."
            )
        elif action == "summarize":
            parts.append(
                "المطلوب: لخّص الدرس أعلاه في نقاط رئيسية قصيرة بالاعتماد على السياق فقط."
            )
        parts.append(f"سؤال الطالب: {question}")
        return "\n\n".join(parts)

    def answer(
        self,
        question: str,
        context_blocks: list[str],
        action: str = "ask",
        student_level: str | None = None,
    ) -> tuple[str, bool]:
        """يرجع (الإجابة, grounded). بلا سياق مناسب → رسالة عدم الكفاية دون ادعاء."""
        if not context_blocks and action == "ask":
            return INSUFFICIENT_CONTENT_MESSAGE, False
        if not context_blocks:
            return INSUFFICIENT_CONTENT_MESSAGE, False
        user_prompt = self.build_user_prompt(question, context_blocks, action, student_level)
        answer = self.provider.complete(SYSTEM_PROMPT_AR, user_prompt)
        return answer, True

    def confirm_answer(
        self,
        question_text: str,
        direct_answer: str,
        context_blocks: list[str],
    ) -> tuple[str, str]:
        """تأكيد/تصحيح الحل المباشر بالاعتماد على سياق الدروس — ترجع (الإجابة، الشرح)."""
        context = "\n\n".join(f"[مقطع {i}]\n{b}" for i, b in enumerate(context_blocks, 1))
        user_prompt = (
            "السياق المسترجع من دروس المنصة:\n" + context +
            f"\n\nسؤال الطالب: {question_text}"
            f"\n\nالحل المباشر المقترح: {direct_answer}"
            "\n\nالمطلوب: راجع الحل المباشر بالاعتماد على السياق فقط، وصححه إن كان خاطئًا. "
            "أعد JSON فقط بهذا الشكل تمامًا وبدون أي شرح خارج JSON: "
            '{"correct_answer": "...", "explanation": "..."}'
        )
        raw = self.provider.complete(SYSTEM_PROMPT_AR, user_prompt)
        content = raw.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content.strip())
        return str(parsed.get("correct_answer", direct_answer)), str(parsed.get("explanation", ""))


def get_ai_service() -> AIService:
    return AIService()
