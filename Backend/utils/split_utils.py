import re

def split_jsp(html: str):
    # JSP에서 Java 코드만 추출
    java_blocks = re.findall(r'<%[=!\-]?([\s\S]*?)%>', html)
    html_only = re.sub(r'<%[=!\-]?[\s\S]*?%>', '', html)
    js_blocks = re.findall(r'<script[\s\S]*?>([\s\S]*?)<\/script>', html_only, re.IGNORECASE)
    css_blocks = re.findall(r'<style[\s\S]*?>([\s\S]*?)<\/style>', html_only, re.IGNORECASE)
    java_code = "\n".join(java_blocks)
    js_code = "\n".join(js_blocks)
    css_code = "\n".join(css_blocks)
    return html_only, java_code, js_code, css_code

def split_aspx(html: str):
    # ASPX: C# 코드 블록 추출
    cs_blocks = re.findall(r'<script\s+runat="server"[\s\S]*?>([\s\S]*?)<\/script>', html, re.IGNORECASE)
    html_only = re.sub(r'<script\s+runat="server"[\s\S]*?>([\s\S]*?)<\/script>', '', html, flags=re.IGNORECASE)
    js_blocks = re.findall(r'<script(?![^>]*runat="server")[\s\S]*?>([\s\S]*?)<\/script>', html_only, re.IGNORECASE)
    css_blocks = re.findall(r'<style[\s\S]*?>([\s\S]*?)<\/style>', html_only, re.IGNORECASE)
    cs_code = "\n".join(cs_blocks)
    js_code = "\n".join(js_blocks)
    css_code = "\n".join(css_blocks)
    return html_only, cs_code, js_code, css_code

def split_html(html: str):
    # <script> 내부 js 추출
    js_blocks = re.findall(r'<script[\s\S]*?>([\s\S]*?)<\/script>', html, re.IGNORECASE)
    # <style> 내부 css 추출
    css_blocks = re.findall(r'<style[\s\S]*?>([\s\S]*?)<\/style>', html, re.IGNORECASE)
    # <script>, <style> 블록 제거한 html만 남기기
    html_only = re.sub(r'<script[\s\S]*?>([\s\S]*?)<\/script>', '', html, flags=re.IGNORECASE)
    html_only = re.sub(r'<style[\s\S]*?>([\s\S]*?)<\/style>', '', html_only, flags=re.IGNORECASE)
    js_code = "\n".join(js_blocks)
    css_code = "\n".join(css_blocks)
    return html_only, js_code, css_code