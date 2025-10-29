from core.graph import build_issue_graph
from dotenv import load_dotenv

load_dotenv(".env")

if __name__ == "__main__":
    app = build_issue_graph()
    result = app.invoke({"user_query": "程序报错了怎么办？"})
    print(result)
