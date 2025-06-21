from fastapi import APIRouter, UploadFile, File, Form
from utils.formatters import format_sql_extended, format_block_style_extended, format_html

router = APIRouter()

@router.post("/format/")
async def format_code(
    file: UploadFile = File(...),
    indent: str = Form("4"),
    brace: str = Form("same-line"),
    comma: str = Form("leading")
):
    code = (await file.read()).decode("utf-8")
    ext = file.filename.split(".")[-1].lower()

    def get_indent() -> str:
        if indent == "tab":
            return "\t"
        return " " * int(indent)

    if ext == "sql":
        result = format_sql_extended(code, get_indent, comma)
    elif ext in ("java", "js", "ts", "py", "c", "cpp"):
        result = format_block_style_extended(code, get_indent, brace)
    elif ext in ("jsp", "html"):
        result = format_html(code, format_block_style_extended, get_indent, brace)
    else:
        result = format_block_style_extended(code, get_indent, brace)

    return {"formatted": result}