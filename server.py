from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
from graphs.issue_graph import build_issue_graph
from core.issue_state import IssueState
from dotenv import load_dotenv
import time
import requests
import os

from agents.review_agent import review_agent

# === 初始化环境 ===
load_dotenv(".env")

app = FastAPI(title="Issue Assistant Webhook")
graph = build_issue_graph()

# === GitHub Access Token（必须配置）===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class IssueWebhook(BaseModel):
    action: str
    issue: dict
    repository: dict
    sender: dict


def fetch_issue_comments(repo_full_name: str, issue_number: int):
    """拉取 Issue 评论"""
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        comments_data = resp.json()
        # 提取文本内容
        return [c["body"] for c in comments_data if "body" in c]
    except Exception as e:
        print(f"⚠️ 拉取评论失败: {e}")
        return []


async def process_issue(issue_state: IssueState):
    """后台执行的Graph处理逻辑"""
    print(f"⚙️ 开始后台处理 Issue #{issue_state['issue_id']}")
    start = time.time()
    result = await graph.ainvoke(issue_state)
    print(f"✅ 处理完成，耗时 {time.time() - start:.2f}s")
    print(f"🔄 上下文: {issue_state}")
    print(f"🔍 分类结果: {result.get('category', 'No category')}")
    print(f"📝 回复内容: {result.get('reply_text', 'No reply')}")
    print(f"🔄 是否需要回复: {result.get('need_reply', False)}")
    print(f"🔍 分类原因: {result.get('reason', 'No reason')}")

    issue_url = issue_state.get('issue_url', 'Unknown URL')
    reply_text = result.get('reply_text', 'No reply')
    
    message = f"issue_url: {issue_url}\n我的回复: {reply_text}"
    
    await review_agent(message)



@app.post("/webhook")
async def handle_issue_webhook(payload: IssueWebhook, background_tasks: BackgroundTasks):
    """GitHub Issue Webhook 入口"""
    data = payload.dict()
    issue = data["issue"]
    issue_number = issue.get("number")
    repo_name = data["repository"]["full_name"]

    print("="*50)
    print(f"📬 收到 Webhook: {data['action']} on {repo_name}#{issue_number}")
    print(f"🔗 Issue URL: {issue.get('html_url')}")
    # 拉取评论
    comments = fetch_issue_comments(repo_name, issue_number)
    print(f"💬 拉取到 {len(comments)} 条评论")

    # 构造 IssueState
    issue_state = IssueState(
        issue_url=issue.get("html_url", ""),
        issue_id=str(issue_number),
        issue_title=issue.get("title", ""),
        issue_body=issue.get("body", ""),
        comments=comments,
        need_reply=True,
    )

    if data['action'] in ['created', 'opened']:
        background_tasks.add_task(process_issue, issue_state)

    # 快速返回响应
    return {
        "status": "accepted",
        "message": f"Issue #{issue_number} 正在后台处理中 🚀",
        "comments_count": len(comments)
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Issue Assistant is running 🚀"}
