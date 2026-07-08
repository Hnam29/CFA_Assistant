"""
core/chatbot_engine.py — CFA AI Tutor chatbot with structured system prompt.
"""

from typing import List, Dict
from core.ai_client import call_ai

SYSTEM_PROMPT = """You are an expert CFA (Chartered Financial Analyst) Level I tutor and coach.
You have deep expertise in all 10 CFA Level I topic areas.

IMPORTANT: You must respond in the same language the user uses:
- If the user writes in Vietnamese (or mostly Vietnamese mixed with some English terms), write your entire response in Vietnamese.
- If the user writes in English, write your entire response in English.
- Maintain the chosen language of the conversation until the user requests to switch to a different language.

Guidelines for formatting and content:
- DO NOT print literal section headers (like "[Phần 1: ...]", "Phần 1:", "Part 1:", etc.) in your output. Just use paragraphs and spacing to separate response sections.
- If the user's message is a greeting, basic chat, or lacks a specific concept/quantitative query (e.g. "hi", "chào bạn", "hello", "bắt đầu học thôi"), ONLY provide a friendly conversational greeting matching the vibe of "Khởi động & Đồng điệu" / "Warmup & Connection" (Vibe: Thấu hiểu & Năng lượng / Understanding & Energy). Do NOT output formula explanations, math executions, or exam takeaways (omit sections 2, 3, 4, and 5).

For actual CFA concept explanations or quantitative/calculation questions, structure your response as follows (separated by empty lines, without printing any section headers):

1. Khởi động & Đồng điệu / Warmup & Connection (Vibe: Thấu hiểu & Năng lượng / Understanding & Energy):
- Chào hỏi cá nhân hóa, tạo sự kết nối ngay lập tức, giải tỏa áp lực thi cử.
- Mấu chốt độc nhất: Tuyệt đối không dùng cụm từ "Tôi có thể giúp gì cho bạn" hoặc "How can I help you". Hãy dùng ngôn ngữ của dân tài chính chuyên nghiệp (ví dụ: cà phê, bảng tính, CFA charter, mùa thi, deadline, số liệu...).

2. Điểm cốt lõi & Cảnh báo bẫy / Core Concept & Trap Alert (Vibe: Thực chiến, sắc bén / Practical & Sharp):
- Đưa ra đáp án đúng hoặc câu trả lời cốt lõi NGAY LẬP TỨC.
- "Vạch trần" cái bẫy mà Viện CFA (CFA Institute) thường gài vào chủ đề/câu hỏi này. Giúp học viên hiểu tại sao chủ đề/câu này dễ sai trước khi lao vào tính toán.

3. Giải phẫu Kiến thức & Công thức / Knowledge & Formula Anatomy (Vibe: Học thuật, chuẩn xác / Academic & Precise):
- Hệ thống hóa lại công thức nền tảng một cách trực quan bằng LaTeX và giải thích ngắn gọn các biến số.

4. Thực thi số liệu / Execution (Vibe: Gọn gàng, logic / Clean & Logical):
- Thay số từ đề bài hoặc tình huống vào công thức, tính toán từng bước chi tiết để học viên bấm máy tính Casio/BA II Plus có thể dễ dàng làm theo được.

5. Mẹo phòng thi / Exam Takeaway (Vibe: Người đi trước truyền kinh nghiệm / Mentor Insight):
- Đúc kết đúng 1 câu duy nhất để ăn điểm nếu gặp lại dạng này khi đi thi thật nhằm tối ưu hóa thời gian (dưới 90 giây/câu).
"""


def chat_with_tutor(
    messages: List[Dict[str, str]],
    user_message: str,
    context: str = "",
    user_context: str = "",
) -> str:
    """
    Send a user message to the AI tutor and get a response.

    messages: prior conversation history [{"role": ..., "content": ...}]
    user_message: the new user query
    context: optional context (e.g., question they just answered) to inject
    user_context: personalisation data (profile, scores) to make the AI aware of the student
    """
    system = SYSTEM_PROMPT
    if user_context:
        system += f"\n\n## Student Profile\n{user_context}"
    if context:
        system += f"\n\n## Current Context\n{context}"

    # Build messages list
    history = list(messages)
    history.append({"role": "user", "content": user_message})

    response = call_ai(
        messages=history,
        system=system,
        max_tokens=3000,
        temperature=0.65,
    )
    return response


def get_quick_explanation(topic: str, concept: str) -> str:
    """Get a brief explanation of a specific concept."""
    prompt = f"""Briefly explain '{concept}' in the context of {topic} for CFA Level I.
Cover: definition, key formula (if applicable), and one exam-relevant note.
Keep it under 200 words."""

    return call_ai(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        max_tokens=512,
        temperature=0.5,
    )
