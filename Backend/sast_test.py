import subprocess, tempfile, os, uuid, requests

SEM_GREP_RULES_PATH = "D:/003_Develop/05_Python/97.semgrep-rules/generic"  # 원하는 경로로 변경

def semgrep_scan_code(code: str, ext: str) -> str:    
    EXT_MAP = {
        "java": "main.java",
        "js": "main.js",
        "html": "main.html",
        "py": "main.py",
        "jsp": "main.jsp",
        "cs": "main.cs",
        "aspx": "main.aspx"
    }
    filename = EXT_MAP.get(ext, f"main.{ext}")
    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        scan = subprocess.run(
            ["semgrep", f"--config={SEM_GREP_RULES_PATH}", "--json", src_path],
            capture_output=True, text=True, encoding="utf-8"
        )

        if scan.returncode != 0 and not scan.stdout:
            return "[Semgrep 실행 오류]\n" + scan.stderr
        import json
        try:
            findings = json.loads(scan.stdout)
            if not findings.get("results"):
                return "[Semgrep 취약점 없음]"
            summary = "\n".join(
                f"- {r['check_id']} : {r['message']} (line {r['start']['line']})"
                for r in findings["results"][:5]
            )
            return summary
        except Exception as e:
            return "[Semgrep 결과 파싱 오류] " + str(e)

if __name__ == "__main__":
    # 분석할 파일명 (sample.jsp)
    file_path = "D:/003_Develop/05_Python/sample.jsp"
    #file_path = "D:/003_Develop/05_Python/13_CodeReview/Backend/convert_to_utf8.py"

    # 파일 읽기
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 확장자 지정 (jsp)
    ext = "jsp"

    print("정적분석 시작...")

    # 정적분석 실행
    result = semgrep_scan_code(code, ext)
    print("[정적분석 결과]")
    print(result)

