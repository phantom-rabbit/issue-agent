# nodes/fetch_issue_node.py
import json
from typing import Any
from core.mcp_manager import MCPManager


class FetchIssueNode:
    """
    Node: 使用 MCP fetch 工具从指定 URL 获取 Issue 内容。

    输入 state:
        {
            "issue_url": "https://github.com/xxx/xxx/issues/123"
        }

    输出 state:
        {
            "issue_url": "...",
            "issue_title": "...",
            "issue_body": "...",
            "comments": [...],
            "raw_content": "完整网页内容"
        }
    """

    def __init__(self):
        self.mcp_manager = MCPManager()

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        issue_url = state.get("issue_url")
        if not issue_url:
            raise ValueError("❌ FetchIssueNode: state 中缺少 issue_url")

        print(f"🌐 [FetchIssueNode] Fetching issue from: {issue_url}")

        # 1️⃣ 获取 MCP fetch 工具
        fetch_tool = await self.mcp_manager.get_tool_by_name("fetch")

        # 2️⃣ 调用 fetch 工具
        try:
            result = await fetch_tool.ainvoke({
                "url": issue_url,
                "raw": True,           # 尝试返回 Markdown 化内容
            })
        except Exception as e:
            print(f"❌ [FetchIssueNode] 调用 MCP 失败: {e}")
            state["fetch_error"] = str(e)
            return state

        # 3️⃣ 解析结果
        content = self._normalize_result(result)
        state["raw_content"] = content

        # 4️⃣ 提取结构化字段（粗略版）
        title = self._extract_title(content)
        body = self._extract_body(content)
        comments = self._extract_comments(content)

        # 5️⃣ 更新 Graph State
        state.update({
            "issue_title": title,
            "issue_body": body,
            "comments": comments,
        })

        print(f"✅ [FetchIssueNode] 成功获取 Issue: {title[:60]}...")
        return state

    # -----------------------
    # 辅助方法
    # -----------------------

    def _normalize_result(self, result: Any) -> str:
        """将 MCP fetch 工具的返回内容标准化为字符串"""
        if isinstance(result, dict):
            if "content" in result:
                return result["content"]
            elif "data" in result:
                return json.dumps(result["data"], ensure_ascii=False, indent=2)
        return str(result)

    def _extract_title(self, text: str) -> str:
        """简单从文本中提取 Issue 标题"""
        for line in text.splitlines():
            if line.strip():
                return line.strip()[:120]
        return "Unknown Issue Title"

    def _extract_body(self, text: str) -> str:
        """取出前几段正文"""
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return "\n\n".join(parts[:3])

    def _extract_comments(self, text: str) -> list[str]:
        """简单提取评论（可以后续用正则或HTML解析替代）"""
        lines = text.splitlines()
        comments = [l.strip() for l in lines if "@" in l or "comment" in l.lower()]
        return comments[:5]
