SYSTEM_PROMPT = """
You classify Vietnamese/English chat messages for a VSTEP study bot.
Return only valid JSON with this schema:
{
  "intent": "vocab_request | quiz_request | task1_request | task2_request | check_writing | upgrade_sentence | explain_sentence | explain_phrase | study_plan | mistake_review | template_request | casual_motivation | general_chat",
  "confidence": 0.0,
  "extracted_text": "",
  "topic": "",
  "task_type": "",
  "should_ask_followup": false,
  "followup_question": ""
}

Prefer practical intent detection. Do not over-classify unclear messages.
If unclear, use general_chat with confidence below 0.55.
""".strip()


def build_intent_classification_messages(text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]

