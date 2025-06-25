import os
from pathlib import Path
import subprocess
import tempfile
import json

# 📁 Semgrep 룰셋 위치
SEM_GREP_RULES_PATH = "D:/003_Develop/05_Python/97.semgrep-rules/"

# 📌 확장자 → 룰 폴더 매핑
RULE_LANG_MAP = {
    "java": "java",
    "js": "javascript",
    "html": "html",
    "py": "python",
    "cs": "csharp"
}

# 📌 임시 파일 확장자 매핑
EXT_MAP = {
    "java": "main.java",
    "js": "main.js",
    "html": "main.html",
    "py": "main.py",
    "jsp": "main.jsp",
    "cs": "main.cs",
    "aspx": "main.aspx"
}

# 🔍 Semgrep 정적 분석 실행 함수
def semgrep_scan_code_detail(code: str, ext: str) -> str:
    rule_subdir = RULE_LANG_MAP.get(ext, None)
    config_path = os.path.join(SEM_GREP_RULES_PATH, rule_subdir) if rule_subdir else SEM_GREP_RULES_PATH
    filename = EXT_MAP.get(ext, f"main.{ext}")

    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        scan = subprocess.run(
            ["semgrep", f"--config={config_path}", "--json", src_path],
            capture_output=True, text=True, encoding="utf-8"
        )

        if scan.returncode != 0 and not scan.stdout:
            return "[Semgrep 실행 오류]\n" + scan.stderr

        try:
            findings = json.loads(scan.stdout)
            results = findings.get("results", [])
            parse_time = (
                findings.get("time", {})
                .get("profiling_times", {})
                .get("total_time", 0.0)
            )

            parseTime = f"\n⏱️ 분석 소요 시간: {parse_time:.3f}초"

            if not results:
                print(f"⏱️ 분석 소요 시간: {parse_time:.3f}초")
                return None  # 취약점 없을 경우

            formatted = []
            for r in results:
                extra = r.get("extra", {})
                meta = extra.get("metadata", {})
                formatted.append(f"""🔢 라인: {r['start'].get('line', '?')}
⚠️ 심각도: {extra.get('severity', '정보없음')}
💬 설명: {extra.get('message', 'No message')}
📚 관련: {", ".join(meta.get('cwe', []) + meta.get('owasp', []))}
🔗 링크:
{chr(10).join(meta.get('references', [])) if meta.get('references') else '-'}{parseTime}
""")
            return "\n---\n".join(formatted)

        except Exception as e:
            return "[Semgrep 결과 파싱 오류]\n" + str(e)

# 📂 폴더 내 Java 소스 파일 전체 분석
def analyze_java_folder(root_folder):
    java_files = list(Path(root_folder).rglob("*.java"))
    total = len(java_files)
    log_lines = []

    if total == 0:
        msg = "📭 분석할 Java 파일이 없습니다."
        print(msg)
        log_lines.append(msg)
        return

    start_msg = f"🔍 총 {total}개 Java 파일 분석 시작"
    print(start_msg)
    log_lines.append(start_msg)

    for idx, file_path in enumerate(java_files, 1):
        progress_msg = f"정적분석 진행중 : {idx} / {total} → {file_path.name}"
        print(progress_msg)
        log_lines.append(progress_msg)

        with open(file_path, encoding="utf-8", errors="ignore") as f:
            code = f.read()

        result = semgrep_scan_code_detail(code, "java")

        if result:
            rel_path = file_path.relative_to(root_folder).with_suffix('')  # .java 제거
            result_file = "_".join(rel_path.parts) + ".txt"
            with open(result_file, "w", encoding="utf-8") as out:
                out.write(result)

            done_msg = f"정적분석 결과 생성 완료: {result_file}"
            print(done_msg)
            log_lines.append(done_msg)
        else:
            clean_msg = "[✅ 취약점 없음]"
            print(clean_msg)
            log_lines.append(clean_msg)

    finish_msg = "✅ 모든 파일 분석 완료!"
    print(finish_msg)
    log_lines.append(finish_msg)

    # 🔸 로그 저장
    with open("total_summary.txt", "w", encoding="utf-8") as summary:
        summary.write("\n".join(log_lines))


# 🚀 실행 시작점
if __name__ == "__main__":
    # 여기에서 분석할 경로를 지정하세요
    target_path = "D:/003_Develop/recruit_java"
    analyze_java_folder(target_path)
