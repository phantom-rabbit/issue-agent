# agents/reply_agent.py
from langchain_core.messages import HumanMessage, SystemMessage
from core.llm import get_llm
from core.issue_state import IssueState

class ReplyAgent:
    """
    Issue 回复生成 Agent
    根据检索结果与当前 Issue 内容，自动生成专业、简洁的回复。
    """

    def __init__(self):
        self.llm = get_llm()

    def run(self, state: IssueState) -> IssueState:
        """
        基于上下文 + 检索内容生成回复
        """
        issue_title = state.get("issue_title", "")
        issue_body = state.get("issue_body", "")
        retrieved_docs = state.get("retrieved_docs", [])

        # 拼接上下文内容
        related_context = ""
        for i, doc in enumerate(retrieved_docs[:5]):
            related_context += f"\n[相似问题{i+1}]\n标题: {doc.metadata.get('title', 'N/A')}\n内容: {doc.page_content[:500]}...\n"

        system_prompt = (
            "你是一名资深的 GitHub 项目维护者，擅长用中文回答技术问题。\n"
            "你的回复必须明确指出问题所在，不能泛泛而谈。\n"
            "明确说明回复给哪个用户，不能回复给所有用户。或者是那个comment\n"
            "根据当前 Issue 和历史相似问题内容，生成一个专业、友好、简洁的回复。\n"
            "要求回复自然、有帮助，可以直接用于评论区。"
        )

        human_prompt = f"""
# Issue标题
{issue_title}

# Issue内容
{issue_body}

# 检索到的相似问题
{related_context if related_context else "（未检索到相似问题）"}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            reply = self.llm.invoke(messages).content.strip()
        except Exception as e:
            reply = f"LLM 生成回复失败: {e}"

        state["reply_text"] = reply
        print("💬 生成回复:\n", reply)
        return state


def reply_node(state: IssueState) -> IssueState:
    """Graph节点包装"""
    agent = ReplyAgent()
    return agent.run(state)


if __name__ == "__main__":
    from langchain_core.documents import Document

    docs = [
        Document(page_content="你可以通过 csghub 的模型管理页面新建模型。",
                 metadata={"title": "如何创建模型"}),
        Document(page_content="目前暂不支持微调模型，但可以导入已有模型。",
                 metadata={"title": "关于微调模型支持"})
    ]

    state = IssueState(
        issue_title="如何在 csghub 中创建可以微调的模型？",
        issue_body="我想在 csghub 中创建一个可以微调的模型，但是不知道从哪里开始。",
        retrieved_docs=docs,
        need_reply=True
    )

    agent = ReplyAgent()
    result = agent.run(state)
    print("🧩 最终输出：", result["reply_text"])
