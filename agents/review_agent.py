import os
import json
import asyncio
import aiohttp
from core.llm import fast
from fast_agent.agents.agent_types import AgentConfig
from fast_agent.agents.tool_agent import ToolAgent
from fast_agent.context import Context


async def send_feishu_message(content: str, webhook_url: str = "https://open.feishu.cn/open-apis/bot/v2/hook/874bf562-1ee7-4143-bc15-2481e42cff03") -> str:
    async with aiohttp.ClientSession() as session:
        payload = {
            "msg_type": "text",
            "content": {"text": content}
        }
        async with session.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        ) as response:
            res_text = await response.text()
            return res_text


class CustomToolAgent(ToolAgent):
    def __init__(
        self,
        config: AgentConfig,
        context: Context | None = None,
    ):
        tools = [send_feishu_message]
        super().__init__(config, tools, context)


instruction = """
你是一个 GitHub issue 回复助手。
你的目标是判断程序生成的回复是否能解决ISSUE问题。
- 如果回复为: No reply，则根据ISSUE上下文判断是否需要通知管理员。
- 如果回复能解决ISSUE问题，请调用 `github-issues-server` 工具来回复。
- 如果恢复不能解决ISSUE问题，请调用 `send_feishu_message` 工具，通知管理员，说明原因和 issue 链接。

通知管理员需要解释通知原因，包括不能解决的问题和 issue 链接。
"""

@fast.custom(
    cls=CustomToolAgent,
    model=os.getenv("OPENAI_API_MODEL"), 
    api_key=os.getenv("OPENAI_API_KEY"), 
    instruction=instruction, servers=["fetch", "github-issues-server"],
    tools=[send_feishu_message],
    )
async def review_agent(message: str):
    async with fast.run() as agent:
        result = await agent.send(message)
        print("模型决策输出：", result)
        return result


# =========================
# 运行
# =========================
async def main():
    message = "用户提了一个无法匹配FAQ的问题，请判断是否要通知管理员。"
    await review_agent(message)

if __name__ == "__main__":
    asyncio.run(main())
