import os
import argparse
from github import Github
from tqdm import tqdm
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings


class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = "BAAI/bge-small-zh"):
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str):
        return self.model.encode(text)

    def embed_documents(self, texts: list[str]):
        return self.model.encode(texts)


def fetch_github_issues(repo_name: str, max_pages: int = 3, token: str = None, per_page: int = 10):
    """
    从指定仓库获取 issue 列表（含标题、正文、评论）
    使用单一进度条显示进度，分页逻辑与 per_page 参数一致。
    """
    g = Github(token or os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    all_issues = []

    tqdm.write(f"🔍 正在拉取仓库 {repo_name} 的 Issues（最多 {max_pages} 页，每页 {per_page} 条）...")

    max_count = max_pages * per_page
    issues = repo.get_issues(state="all", direction="desc", sort="created")
    pbar = tqdm(total=max_count, desc="📥 拉取 Issues", unit="条", dynamic_ncols=True)

    try:
        for page in range(1, max_pages + 1):
            issues_page = issues.get_page(page - 1)
            if not issues_page:
                break

            tqdm.write(f"📄 第 {page} 页，共 {len(issues_page)} 条")

            for issue in issues_page:
                if getattr(issue, "pull_request", None):
                    continue

                comments = [c.body for c in issue.get_comments()]
                text = f"# {issue.title}\n\n{issue.body or ''}\n\n" + "\n".join(comments)

                all_issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "comments": comments,
                    "content": text,
                })

                pbar.update(1)
                if len(all_issues) >= max_count:
                    break

            if len(all_issues) >= max_count:
                break

    finally:
        pbar.close()

    tqdm.write(f"📦 已拉取 {len(all_issues)} 条 Issue（共 {page} 页）")
    return all_issues


# ===== 构建 Chroma 向量数据库 =====
def build_vector_db(repo_name: str, persist_dir: str = "data/chroma", max_pages: int = 3, token: str = None):
    """
    拉取历史 Issue 并构建 Chroma 向量数据库
    """
    issues = fetch_github_issues(repo_name, max_pages=max_pages, token=token)
    print(f"📦 拉取完成，共 {len(issues)} 条 Issue")

    # === 构建 LangChain 文档对象 ===
    docs = [Document(page_content=i["content"], metadata={"title": i["title"], "id": i["number"]}) for i in issues]

    # === 文本切分 ===
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)
    print(f"✂️ 已分割为 {len(split_docs)} 条文本块，开始生成向量...")

    # === 向量模型 ===
    embeddings = LocalEmbeddings("BAAI/bge-small-zh")

    # === 生成向量 ===
    texts = [d.page_content for d in split_docs]
    metadatas = [d.metadata for d in split_docs]

    vectors = []
    for text in tqdm(texts, desc="🧠 正在生成向量", unit="段"):
        vector = embeddings.embed_query(text)
        vectors.append(vector)

    print("💾 正在保存向量数据库...")

    # === 使用 Chroma 存储 ===
    db = Chroma(
        collection_name="issues",
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

    # 逐条写入（带进度条）
    for text, meta in tqdm(zip(texts, metadatas), total=len(texts), desc="📚 写入 Chroma", dynamic_ncols=True):
        db.add_texts([text], metadatas=[meta])

    print(f"✅ 向量数据库已保存至：{persist_dir}")
    return db


# ===== 命令行入口 =====
def main():
    parser = argparse.ArgumentParser(description="构建 GitHub Issue 向量知识库")
    parser.add_argument("--repo", default="OpenCSGs/csghub", help="GitHub 仓库名，例如 OpenCSGs/csghub")
    parser.add_argument("--persist_dir", default="data/chroma", help="向量数据库保存目录")
    parser.add_argument("--max_pages", type=int, default=3, help="最大拉取页数")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub Token，可使用环境变量")

    args = parser.parse_args()

    print(f"🚀 开始构建知识库：{args.repo}")
    build_vector_db(
        repo_name=args.repo,
        persist_dir=args.persist_dir,
        max_pages=args.max_pages,
        token=args.token
    )


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv(".env")
    main()
