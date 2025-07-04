import re

def clean_text(text: str, max_words: int = 200) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "http", text)   # replace URLs
    text = re.sub(r"@\w+", "@user", text)     # replace @mentions
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace
    text = " ".join(text.split()[:max_words]) # limit to max_words

    return text

def extract_hashtags(text: str) -> list[str]:
    """
    Extracts hashtags from text, returns them as a list keeping the # symbol.
    """
    hashtags = re.findall(r"#\w+", text)
    return hashtags