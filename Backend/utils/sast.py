import subprocess, tempfile, os, uuid, requests, json
from .gpt_sidekick import format_findings_with_gpt_bulk, format_finding_with_gpt

SEM_GREP_RULES_PATH = "D:/003_Develop/05_Python/97.semgrep-rules/"  # 최상위 rules 폴더

RULE_LANG_MAP = {
    "java": "java",
    "js": "javascript",
    "html": "html",
    "py": "python",
    "cs": "csharp"
}

EXT_MAP = {
    "java": "main.java",
    "js": "main.js",
    "html": "main.html",
    "py": "main.py",
    "jsp": "main.jsp",
    "cs": "main.cs",
    "aspx": "main.aspx"
}

def _get_config_path(ext):
    rule_subdir = RULE_LANG_MAP.get(ext)
    if rule_subdir:
        return os.path.join(SEM_GREP_RULES_PATH, rule_subdir)
    return SEM_GREP_RULES_PATH


def semgrep_scan_code_detail(code: str, ext: str) -> str:
    config_path = _get_config_path(ext)
    print(f"룰 경로 : {config_path}")

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
                return f"[✅ 취약점 없음]\n이 파일에는 Semgrep 룰셋에 해당하는 보안 이슈가 발견되지 않았습니다.{parseTime}"

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

def semgrep_scan_code_detail_with_gpt(
    code: str,
    ext: str,
    use_gpt: bool = False,
    gpt_model: str = "gpt-3.5-turbo"
) -> dict:
    config_path = _get_config_path(ext)
    print(f"룰 경로 : {config_path}")

    filename = EXT_MAP.get(ext, f"main.{ext}")

    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, filename)
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        scan = subprocess.run(
            ["semgrep", f"--config={config_path}", "--json", src_path],
            capture_output=True, text=True, encoding="utf-8"
        )

        #print("====1====")
        if scan.returncode != 0 and not scan.stdout:
            return {"error": "[Semgrep 실행 오류]", "details": scan.stderr}

        #print("====2====")
        try:
            #print("====3====")
            findings_json = json.loads(scan.stdout)
            results = findings_json.get("results", [])
            parse_time = (
                findings_json.get("time", {})
                .get("profiling_times", {})
                .get("total_time", 0.0)
            )

            #print("====4====")

            if not results:
                return {
                    "results": [f"[✅ 취약점 없음]\n이 파일에는 Semgrep 룰셋에 해당하는 보안 이슈가 발견되지 않았습니다."],
                    "parse_time": parse_time
                }

            #print("====5====")

            finding_summaries = []
            for r in results:
                rule = r.get("check_id", "")
                path = r.get("path", "")
                line = r.get("start", {}).get("line", "?")
                message = r.get("extra", {}).get("message", "No message")
                finding_summaries.append(f"[{rule}] {path}:{line} - {message}")
                #print(f"====5-{line}====")

            #print("====6====")

            # GPT 피드백 생성
            #gpt_feedbacks = []

            #if use_gpt:
                #gpt_feedbacks = format_findings_with_gpt_bulk(finding_summaries, gpt_model)

            #print("====7====")

            # 포맷 텍스트 생성
            formatted_results = []
            for idx, r in enumerate(results):
                extra = r.get("extra", {})
                meta = extra.get("metadata", {})
                links = r.get("extra", {}).get("metadata", {}).get("references", [])

                base_text = f"""🔢 라인: {r['start'].get('line', '?')}
⚠️ 심각도: {extra.get('severity', '정보없음')}
💬 설명: {extra.get('message', 'No message')}
📚 관련: {", ".join(meta.get('cwe', []) + meta.get('owasp', []))}
🔗 링크:
{chr(10).join(links) if links else '-'}
"""
                #일괄로 불러오는게 잘 안되어서 건바이건으로 처리
                #if use_gpt and idx < len(gpt_feedbacks):
                    #base_text += f"\n✍️ GPT 개선 제안:\n{gpt_feedbacks[idx]}"
                if use_gpt:
                    base_text += f"\n✍️ GPT 개선 제안:\n{format_finding_with_gpt(finding_summaries[idx], gpt_model)}"
                #print(f"{base_text}")

                formatted_results.append(base_text)
            
            #print("====8====")
            return {
                "results": formatted_results,
                "parse_time": parse_time
            }

        except Exception as e:
            formatted_results = []
            formatted_results.append(f"❌ 오류 메시지\n{str(e)}")
            return {
                "results": formatted_results,
                "parse_time": 0
            }

def semgrep_scan_code(code: str, ext: str) -> str:
    config_path = _get_config_path(ext)
    print(f"룰 경로 : {config_path}")

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
            if not results:
                return "[Semgrep 취약점 없음]"

            summary = ""
            for r in results:
                extra = r.get("extra", {})
                line = r.get("start", {}).get("line", "?")
                message = extra.get("message", "No message")
                summary += f"\n[라인: {line}] {message}\n"

            return summary.strip()

        except Exception as e:
            return "[Semgrep 결과 파싱 오류] " + str(e)

def sonarqube_scan_java_code(code: str, sonar_host: str, sonar_token: str) -> str:
    sonar_project = f"upload-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as tempdir:
        src_path = os.path.join(tempdir, "Main.java")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)
        props_path = os.path.join(tempdir, "sonar-project.properties")
        with open(props_path, "w") as f:
            f.write(f"""
sonar.projectKey={sonar_project}
sonar.sources=.
sonar.java.binaries=.
sonar.sourceEncoding=UTF-8
sonar.host.url={sonar_host}
""")
        scan = subprocess.run(
            ["sonar-scanner", f"-Dsonar.login={sonar_token}"],
            cwd=tempdir, capture_output=True, text=True
        )
        issues_url = f"{sonar_host}/api/issues/search?componentKeys={sonar_project}&resolved=false"
        try:
            import time
            time.sleep(3)
            resp = requests.get(issues_url, auth=(sonar_token, ''))
            if resp.status_code == 200:
                issues = resp.json()
                summary = "\n".join(
                    f"- {item['message']} (Severity: {item['severity']})"
                    for item in issues.get('issues', [])[:5]
                )
                return summary or "[취약점 없음]"
            else:
                return "[SonarQube REST API 결과 조회 실패]"
        except Exception as e:
            return f"[SonarQube 이슈 조회 오류] {str(e)}"
