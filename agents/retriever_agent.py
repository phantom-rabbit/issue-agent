# retriever_agent.py
from langchain_chroma import Chroma
from typing import List
from core.issue_state import IssueState
from scripts.build import LocalEmbeddings

class RetrieverAgent:
    def __init__(self, persist_dir="data/chroma_db", model_name="BAAI/bge-small-zh"):
        self.persist_dir = persist_dir
        self.embeddings = LocalEmbeddings(model_name=model_name)
        self.db = Chroma(
            collection_name="issues",
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )

    def run(self, state: IssueState) -> IssueState:
        """检索与当前 Issue 相关的历史 Issue 或 FAQ"""
        query_text = f"{state['issue_title']}\n{state['issue_body']}"
        results = self.db.similarity_search(query_text, k=5)

        state["retrieved_docs"] = results
        print(f"🔍 检索到 {len(results)} 条相关文档")

        return state


def retriever_node(state: IssueState) -> IssueState:
    """Graph节点包装"""
    agent = RetrieverAgent()
    return agent.run(state)


if __name__ == "__main__":
    agent = RetrieverAgent()
    state = IssueState(
        issue_number=123,
        issue_title="如何上传超过20MB的大文件到Gitlab？",
        issue_body="我想上传一个超过20MB的大文件到Gitlab，但是上传失败。",
        comments=[],
        need_reply=True
    )
    state = agent.run(state)
    print(state)