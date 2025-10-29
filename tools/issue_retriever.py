# tools/issue_retriever.py
import os
import json
import glob

DATA_PATH = "data/issues"

def load_local_issues(max_files: int = 5) -> list[dict]:
    """
    加载本地 Issue 文件，返回列表 [{filename, content}, ...]
    """
    issues = []
    for file in glob.glob(os.path.join(DATA_PATH, "*"))[:max_files]:
        try:
            if file.endswith(".json"):
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    content = data.get("content") or data.get("body", "")
            else:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
            issues.append({"file": file, "content": content.strip()})
        except Exception as e:
            print(f"⚠️ 读取 {file} 失败：{e}")
    return issues
