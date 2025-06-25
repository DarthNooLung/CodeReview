import os

rule_dir = "D:/003_Develop/05_Python/97.semgrep-rules/"
for root, dirs, files in os.walk(rule_dir):
    for fname in files:
        if fname.endswith(".yaml") or fname.endswith(".yml"):
            path = os.path.join(root, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    f.read()
            except Exception as e:
                print(f"[ERROR] {path} -> {e}")
