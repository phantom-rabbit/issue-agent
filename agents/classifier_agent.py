from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict

from urllib3 import request
from core.llm import get_llm
from core.issue_state import IssueState



class ClassifierAgent:
    """
    Issue 评论分类与分析 Agent
    """

    def __init__(self):
        """
        初始化模型，可以替换为 DeepSeek、Moonshot 等兼容OpenAI API的模型。
        """
        self.llm = get_llm()

    def analyze_comments(self, issue_state: IssueState) -> IssueState:
        """
        分析一条 Issue 的评论，判断是否需要回复
        """
        text = "\n".join([f"- {c}" for c in issue_state["comments"]])
        messages = [
            SystemMessage(
                content=(
                "你是一个OpencsgHUb GitHub Issue 分析助手。"
                "任务：阅读所有评论内容，判断该问题是否已解决。"
                "判断规则："
                "1. 如果用户表示问题解决、感谢、关闭等，则 need_reply = false。"
                "2. 如果用户表示问题仍存在、希望帮助、等待回复，则 need_reply = true。"
                "3. 如果有其其他人提供了解决方案但用户尚未确认问题是否解决，则 need_reply = false"
                "输出格式：JSON，如："
                '{"need_reply": true, "reason": "用户表示问题仍未解决", "category": "bug"}'
                )
            ),
            HumanMessage(content=f"以下是Issue的评论内容：\n{text}")
        ]
        try:
            result = self.llm.invoke(messages).content
        except Exception as e:
            result = f'{{"need_reply": false, "reason": "LLM调用失败: {e}", "category": "unknown"}}'
        return self._parse_output(issue_state=issue_state, text=result)

    def _parse_output(self, issue_state: IssueState, text: str) -> IssueState:
        import json, re

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                result = json.loads(match.group(0))
                issue_state.update({
                    "need_reply": bool(result.get("need_reply", False)),
                    "reason": result.get("reason", "未给出原因"),
                    "category": result.get("category", "unknown"),
                })
                return issue_state
            except json.JSONDecodeError:
                pass

        # 如果LLM输出无法解析，返回兜底
        issue_state.update({
            "need_reply": False,
            "reason": f"无法解析模型输出: {text[:100]}...",
            "category": "parse_error"
        })
        return issue_state


from agents.classifier_agent import ClassifierAgent
def classify_node(state: IssueState):
    agent = ClassifierAgent()
    return agent.analyze_comments(state)

if __name__ == "__main__":
    import json
    import requests
    result = requests.get("https://api.github.com/repos/phantom-rabbit/mengyao/issues/23/comments")
    result = json.loads(result.text)
    
    print(result)

    agent = ClassifierAgent()
    comments = result
    issue_state = IssueState(
        issue_id="123",
        comments=comments,
        need_reply=False,
        reply_content=None,
        context_from_history=None,
        context_from_faq=None,
        notified=False
    )
    result = agent.analyze_comments(issue_state)
    print(result)
