from html import escape


SOCIAL_MEDIA_NEGATIVE_CHILDREN_PHRASES = [
    {
        "phrase": "excessive screen time",
        "meaning": "thời gian nhìn màn hình quá mức",
        "example": "Excessive screen time can reduce children's concentration and affect their sleep.",
        "usage": "Dùng để nói về tác hại trực tiếp của mạng xã hội lên sức khỏe và học tập.",
    },
    {
        "phrase": "be exposed to harmful content",
        "meaning": "tiếp xúc với nội dung độc hại",
        "example": "Children may be exposed to harmful content if they use social media without guidance.",
        "usage": "Dùng tốt trong body paragraph nói về rủi ro online.",
    },
    {
        "phrase": "cyberbullying",
        "meaning": "bắt nạt trên mạng",
        "example": "Cyberbullying can seriously damage children's mental well-being.",
        "usage": "Cụm mạnh cho luận điểm về sức khỏe tinh thần.",
    },
    {
        "phrase": "social comparison",
        "meaning": "sự so sánh bản thân với người khác trên mạng",
        "example": "Social comparison may make teenagers feel insecure about their appearance and lifestyle.",
        "usage": "Dùng khi nói về áp lực tâm lý từ hình ảnh hoàn hảo trên mạng.",
    },
    {
        "phrase": "addictive online content",
        "meaning": "nội dung trực tuyến dễ gây nghiện",
        "example": "Addictive online content can distract children from studying and outdoor activities.",
        "usage": "Dùng để giải thích vì sao trẻ em khó kiểm soát thời gian dùng mạng.",
    },
    {
        "phrase": "reduce face-to-face interaction",
        "meaning": "giảm giao tiếp trực tiếp",
        "example": "Heavy use of social media may reduce face-to-face interaction among children.",
        "usage": "Dùng cho ý về kỹ năng giao tiếp và quan hệ xã hội.",
    },
    {
        "phrase": "lower academic performance",
        "meaning": "làm giảm kết quả học tập",
        "example": "Spending too much time online can lower children's academic performance.",
        "usage": "Dùng khi liên hệ mạng xã hội với việc học.",
    },
    {
        "phrase": "develop unhealthy habits",
        "meaning": "hình thành thói quen không lành mạnh",
        "example": "Children may develop unhealthy habits if they stay online late at night.",
        "usage": "Dùng trong phần tác động dài hạn.",
    },
]


def is_useful_phrase_request(text: str) -> bool:
    lower = text.lower()
    request_markers = [
        "từ hữu dụng",
        "từ hay",
        "cụm hữu dụng",
        "cụm hay",
        "từ dùng",
        "cụm dùng",
        "useful words",
        "useful phrases",
        "một số từ",
        "một số cụm",
    ]
    writing_markers = ["essay", "easy", "viết bài", "viết luận", "writing", "task 2", "dùng cho viết"]
    return any(marker in lower for marker in request_markers) and (
        any(marker in lower for marker in writing_markers) or "nói về" in lower
    )


def build_essay_phrase_pack(text: str) -> str:
    lower = text.lower()
    if "mạng xã hội" in lower or "social media" in lower:
        if "trẻ em" in lower or "children" in lower or "teenager" in lower or "teenagers" in lower:
            return build_social_media_negative_children_pack()
    return build_generic_phrase_pack()


def build_social_media_negative_children_pack() -> str:
    blocks = [
        "📘 <b>Cụm từ hữu dụng cho essay</b>",
        "<b>Topic:</b> Negative effects of social media on children",
        "",
        "Bạn có thể dùng các cụm này cho Task 2 về mạng xã hội, trẻ em, giáo dục và sức khỏe tinh thần.",
    ]

    for index, item in enumerate(SOCIAL_MEDIA_NEGATIVE_CHILDREN_PHRASES, start=1):
        blocks.extend(
            [
                "",
                f"<b>{index}. {escape(item['phrase'])}</b>",
                f"🇻🇳 Nghĩa: {escape(item['meaning'])}",
                f"🧩 Example: <i>{escape(item['example'])}</i>",
                f"✍️ Usage: {escape(item['usage'])}",
            ]
        )

    blocks.extend(
        [
            "",
            "🧠 <b>Useful sentence patterns</b>",
            "• Social media can have a negative impact on children's mental well-being.",
            "• Excessive use of social media may lead to lower academic performance.",
            "• Parents should provide guidance to help children use social media safely.",
            "",
            "📝 <b>Sample body paragraph</b>",
            "<i>One major disadvantage of social media is that it can negatively affect children’s mental well-being. "
            "For example, many teenagers compare themselves with unrealistic images online, which may make them feel insecure. "
            "In addition, excessive screen time can distract children from studying and reduce face-to-face interaction. "
            "Therefore, parents should provide guidance and set healthy limits on social media use.</i>",
        ]
    )
    return "\n".join(blocks)


def build_generic_phrase_pack() -> str:
    return "\n".join(
        [
            "📘 <b>Cụm từ hữu dụng cho essay</b>",
            "",
            "Bạn nói rõ topic hơn một chút nhé. Ví dụ:",
            "• từ hữu dụng về tác hại của mạng xã hội lên trẻ em",
            "• cụm hay về environment cho Task 2",
            "• vocab về education dùng cho essay",
        ]
    )

