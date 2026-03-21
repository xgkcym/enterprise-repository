def is_chinese(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)