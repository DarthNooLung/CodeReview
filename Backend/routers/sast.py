from fastapi import APIRouter, UploadFile, File, Form
from utils.sast import semgrep_scan_code_detail_with_gpt
from utils.security import allowed_file, file_size_okay
from utils.split_utils import split_jsp, split_aspx, split_html

router = APIRouter()

@router.post("/sast/")
async def analyze_code_with_sast_gpt(
    file: UploadFile = File(...),
    use_gpt_feedback: str = Form("false"),
    gpt_model: str = Form("gpt-3.5-turbo")
):
    try:
        if not allowed_file(file.filename):
            return {"error": "[허용되지 않는 확장자]"}

        content = await file.read()
        if not file_size_okay(content):
            return {"error": "[파일 용량이 너무 큽니다]"}

        code = content.decode("utf-8")
        ext = file.filename.split('.')[-1].lower()

        use_gpt = use_gpt_feedback.lower() in ["true", "1", "yes"]
        results = []

        if ext == "jsp":
            html_part, java_part, js_part, css_part = split_jsp(code)

            if html_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(html_part, "html", use_gpt, gpt_model)
                results.append({"language": "HTML", **r})
            if java_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(java_part, "java", use_gpt, gpt_model)
                results.append({"language": "Java", **r})
            if js_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(js_part, "js", use_gpt, gpt_model)
                results.append({"language": "JS", **r})
            if css_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(css_part, "css", use_gpt, gpt_model)
                results.append({"language": "CSS", **r})

        elif ext == "aspx":
            html_part, cs_part, js_part, css_part = split_aspx(code)

            if html_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(html_part, "html", use_gpt, gpt_model)
                results.append({"language": "HTML", **r})
            if cs_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(cs_part, "cs", use_gpt, gpt_model)
                results.append({"language": "C#", **r})
            if js_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(js_part, "js", use_gpt, gpt_model)
                results.append({"language": "JS", **r})
            if css_part.strip():
                r = await semgrep_scan_code_detail_with_gpt(css_part, "css", use_gpt, gpt_model)
                results.append({"language": "CSS", **r})

        elif ext in ["java", "js", "py", "cs", "css"]:
            r = await semgrep_scan_code_detail_with_gpt(code, ext, use_gpt, gpt_model)
            results.append({"language": ext, **r})

        else:
            return {"error": "[지원되지 않는 파일 유형이거나 SAST 분석 불가]"}

        return {"sast_result": results}

    except Exception as e:
        return {
            "error": "[서버 처리 오류]",
            "details": str(e)
        }
