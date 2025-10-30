# retriever_agent.py
from langchain_chroma import Chroma
from typing import List
from core.issue_state import IssueState
from langchain_huggingface import HuggingFaceEmbeddings


class RetrieverAgent:
    def __init__(self, persist_dir="data/chroma", model_name="BAAI/bge-small-zh"):
        self.persist_dir = persist_dir
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
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
        issue_title="如何在csghub中创建可以微调的模型？",
        issue_body="我想在csghub中创建一个可以微调的模型，但是不知道从哪里开始。",
        comments=[],
        need_reply=True
    )
    state = agent.run(state)
    print(state)