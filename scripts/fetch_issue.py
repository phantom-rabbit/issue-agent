import os
import time
from datetime import datetime, timezone
from github import Github, Auth, RateLimitExceededException
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv(".env")

def fetch_github_issues(repo_name: str, max_issues: int = 50, token: str = None):
    """
    拉取 GitHub Issues（含标题、正文、评论）
    - max_issues: 外部调用控制抓取总条数
    - 自动处理速率限制
    - 过滤 PR
    - 避免重复
    """
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("❌ 请在 .env 文件中配置 GITHUB_TOKEN 或传入 token 参数")

    g = Github(auth=Auth.Token(token))
    repo = g.get_repo(repo_name)
    all_issues = []
    seen_numbers = set()
    total_fetched = 0

    tqdm.write(f"🔍 正在拉取仓库 {repo_name} 的 Issues（最多 {max_issues} 条）...")

    issues_iterator = repo.get_issues(state="all", direction="desc", sort="created")
    pbar = tqdm(desc="📥 拉取 Issues", unit="条", dynamic_ncols=True)

    for issue in issues_iterator:
        if total_fetched >= max_issues:
            break
        if getattr(issue, "pull_request", None):  # 过滤 PR
            continue
        if issue.number in seen_numbers:  # 去重
            continue

        while True:
            try:
                comments = [c.body for c in issue.get_comments()]
                break
            except RateLimitExceededException:
                reset_time = g.get_rate_limit().core.reset
                sleep_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds() + 5
                tqdm.write(f"🚦 触发速率限制，等待 {int(sleep_seconds)} 秒后重试")
                time.sleep(sleep_seconds)

        text = f"# {issue.title}\n\n{issue.body or ''}\n\n" + "\n".join(comments)
        all_issues.append({
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "comments": comments,
            "content": text,
        })
        seen_numbers.add(issue.number)

        total_fetched += 1
        pbar.set_postfix({"已拉取": total_fetched})
        pbar.update(1)

    pbar.close()
    tqdm.write(f"📦 已拉取 {len(all_issues)} 条有效 Issue")
    return all_issues


from scripts.faq import generate_issue_faq
   

if __name__ == "__main__":
    repo_name = "OpenCSGs/csghub"
    issues = fetch_github_issues(repo_name, max_issues=2)
    print(f"最终抓取有效 Issue 数量: {len(issues)}")
    faqs = generate_issue_faq(issues)

    print(f"最终生成 FAQ 数量: {len(faqs)}")
    # 保存到 JSON 文件
    import json
    with open("data/issues_faq.json", "w", encoding="utf-8") as f:
        json.dump(faqs, f, ensure_ascii=False, indent=2)