import re

def smart_chunking(code: str, chunk_size: int, language: str = "Plain Text") -> list[str]:
    lang_patterns = {
        "Python": r'(\n(?:def|class)\s+\w+.*?:)',
        "Java": r'(\n\s*(public|private|protected)?\s*(static)?\s*(class|interface|void|\w+)\s+\w+\s*\([^)]*\)\s*\{)',
        "C#": r'(\n\s*(public|private|protected)?\s*(static)?\s*(class|interface|void|\w+)\s+\w+\s*\([^)]*\)\s*\{)',
        "JavaScript": r'(\n\s*(function|class)\s+\w+\s*\([^)]*\)\s*\{)',
        "TypeScript": r'(\n\s*(function|class)\s+\w+\s*\([^)]*\)\s*\{)',
        "C++": r'(\n\s*(class|void|\w+)\s+\w+\s*\([^)]*\)\s*\{)',
    }
    
    pattern = lang_patterns.get(language, r'\n')
    parts = re.split(pattern, code)
    chunks = []
    buffer = ""
    i = 0
    
    while i < len(parts):
        part = parts[i] or ""
        if i + 1 < len(parts):
            part += parts[i + 1] or ""
            i += 2
        else:
            i += 1

        if len(buffer) + len(part) < chunk_size:
            buffer += part
        else:
            if buffer:
                chunks.append(buffer)
            buffer = part

    if buffer:
        chunks.append(buffer)
    return chunks

def smart_chunking_html(code: str, chunk_size: int) -> list[str]:
    parts = code.split('\n')
    chunks = []
    buffer = ""
    for line in parts:
        if len(buffer) + len(line) < chunk_size:
            buffer += line + "\n"
        else:
            chunks.append(buffer)
            buffer = line + "\n"
    if buffer:
        chunks.append(buffer)
    return chunks