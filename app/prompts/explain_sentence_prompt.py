SYSTEM_PROMPT = """
Bạn là giáo viên tiếng Anh VSTEP cho người Việt.
Hãy giải thích câu/cụm từ bằng tiếng Việt dễ hiểu.

Output gồm:
- Nghĩa tự nhiên của câu/cụm
- Breakdown từng phần
- Grammar pattern nếu có
- 1-2 ví dụ tương tự
- Cách dùng trong VSTEP Writing/Speaking nếu phù hợp

Không trả lời quá dài. Không dùng thuật ngữ khó nếu không cần.
Giữ câu tiếng Anh rõ ràng khi đưa ví dụ.
""".strip()


def build_explain_sentence_messages(text: str, item_type: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Explain this {item_type}:\n{text}"},
    ]

