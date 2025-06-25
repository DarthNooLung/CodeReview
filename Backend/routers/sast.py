from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from utils.sast import semgrep_scan_code_detail, semgrep_scan_code_detail
from utils.security import allowed_file, file_size_okay
from utils.split_utils import split_jsp, split_aspx, split_html  # 분리 함수들은 utils로 옮겼다고 가정

router = APIRouter()

@router.post("/sast/")
async def analyze_code_only_sast(file: UploadFile = File(...)):
    try:
        if not allowed_file(file.filename):
            return JSONResponse(status_code=400, content={"error": "허용되지 않는 확장자입니다."})

        content = await file.read()
        if not file_size_okay(content):
            return JSONResponse(status_code=400, content={"error": "파일 용량이 너무 큽니다."})

        code = content.decode("utf-8")
        ext = file.filename.split('.')[-1].lower()

        sast_result = ""
        if ext == "jsp":
            html_part, java_part, js_part, css_part = split_jsp(code)
            sast_result = (
                f"[HTML 분석]\n{semgrep_scan_code_detail(html_part, 'html')}\n\n"
                f"[Java 분석]\n{semgrep_scan_code_detail(java_part, 'java') if java_part.strip() else '[Java 코드 없음]'}\n\n"
                f"[JS 분석]\n{semgrep_scan_code_detail(js_part, 'js') if js_part.strip() else '[JS 코드 없음]'}\n\n"
                f"[CSS 분석]\n{semgrep_scan_code_detail(css_part, 'css') if css_part.strip() else '[CSS 코드 없음]'}"
            )
        elif ext == "aspx":
            html_part, cs_part, js_part, css_part = split_aspx(code)
            sast_result = (
                f"[HTML 분석]\n{semgrep_scan_code_detail(html_part, 'html')}\n\n"
                f"[C# 분석]\n{semgrep_scan_code_detail(cs_part, 'cs') if cs_part.strip() else '[C# 코드 없음]'}\n\n"
                f"[JS 분석]\n{semgrep_scan_code_detail(js_part, 'js') if js_part.strip() else '[JS 코드 없음]'}\n\n"
                f"[CSS 분석]\n{semgrep_scan_code_detail(css_part, 'css') if css_part.strip() else '[CSS 코드 없음]'}"
            )
        elif ext == "html":
            html_only, js_code, css_code = split_html(code)
            sast_result = (
                f"[HTML 분석]\n{semgrep_scan_code_detail(html_only, 'html')}\n\n"
                f"[JS 분석]\n{semgrep_scan_code_detail(js_code, 'js') if js_code.strip() else '[JS 코드 없음]'}\n\n"
                f"[CSS 분석]\n{semgrep_scan_code_detail(css_code, 'css') if css_code.strip() else '[CSS 코드 없음]'}"
            )
        elif ext in ["java", "js", "py", "cs", "css"]:
            sast_result = semgrep_scan_code_detail(code, ext)
        else:
            sast_result = "[지원되지 않는 파일 유형이거나 SAST 분석 불가]"

        return {"sast_result": sast_result}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
