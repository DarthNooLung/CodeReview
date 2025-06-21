def format_sql_extended(code: str, get_indent, comma: str) -> str:
    lines = code.splitlines()
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith(("SELECT", "FROM", "WHERE", "JOIN", "ON", "AND", "OR", "GROUP BY", "ORDER BY")):
            formatted.append("\n" + line)
        elif comma == "leading" and line.startswith(","):
            formatted.append("\n" + line)
        elif comma == "trailing" and line.endswith(","):
            formatted.append(line)
        else:
            formatted.append(get_indent() + line)
    return "\n".join(formatted)

def format_block_style_extended(code: str, get_indent, brace: str) -> str:
    lines = code.splitlines()
    formatted = []
    level = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("}") or stripped.startswith(");") or stripped.startswith("end"):
            level = max(0, level - 1)
        prefix = get_indent() * level
        if brace == "next-line" and "{" in stripped and not stripped.startswith("{"):
            parts = stripped.split("{")
            formatted.append(prefix + parts[0].strip())
            formatted.append(prefix + "{")
        else:
            formatted.append(prefix + stripped)
        if stripped.endswith("{") or stripped.endswith("(") or stripped.endswith("then") or (
            "{" in stripped and "}" not in stripped):
            level += 1
        elif stripped.endswith("begin"):
            level += 1
    return "\n".join(formatted)

def format_html(code: str, format_block_style_extended, get_indent, brace):
    import re
    code = re.sub(r'>\s*<', '>\n<', code)
    return format_block_style_extended(code, get_indent, brace)