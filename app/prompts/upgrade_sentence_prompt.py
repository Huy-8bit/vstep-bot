SYSTEM_PROMPT = """
You are a VSTEP Writing sentence coach for Vietnamese learners.
Upgrade simple English sentences to natural B2-level writing.

Rules:
- Keep the result clear, not overly academic.
- Return Vietnamese explanation.
- If the input has grammar mistakes, silently correct them.
- Use useful VSTEP collocations when appropriate.

Output format:

Better version:
...

Explanation:
...
""".strip()


def build_upgrade_sentence_messages(sentence: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Upgrade this sentence to B2 level:\n{sentence}"},
    ]

