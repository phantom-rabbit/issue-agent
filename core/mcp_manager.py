# # core/mcp_manager.py
# import asyncio
# from typing import Dict, List, Optional

# from langchain_mcp_adapters.client import MultiServerMCPClient
# from core.config_loader import load_config


# class MCPManager:
#     """
#     统一管理 MCP 工具注册与访问（严格版本）。
#     特点：
#       - 按需按名字加载工具（非空校验）
#       - 如果请求 N 个工具但实际只返回 M < N 个，会抛错
#       - 内部缓存已加载的工具（按 name）
#       - 支持可选超时（秒）
#     """

#     def __init__(self, config_path: str = "config/mcp.yaml"):
#         cfg = load_config(config_path)
#         self.config: Dict[str, Dict] = cfg.get("mcp", {}) if cfg else {}
#         self._tool_cache: Dict[str, object] = {}  # name -> StructuredTool

#     async def _create_client(self, subset: Dict[str, Dict]) -> MultiServerMCPClient:
#         """内部：创建 MultiServerMCPClient（不做缓存，具体调用方决定缓存策略）"""
#         if not subset:
#             raise ValueError("MCPManager._create_client(): 工具子集为空，无法创建客户端。")
#         return MultiServerMCPClient(subset)

#     async def get_tools(self, names: List[str], timeout: Optional[float] = None) -> List[object]:
#         """
#         严格按名称加载并返回 MCP 工具列表（顺序不保证）。
#         - names: 非空列表，包含要加载的 MCP 名称
#         - timeout: 可选超时（秒），None 表示不超时
#         返回值：StructuredTool 列表
#         抛错：
#           - ValueError: 参数校验失败或配置中没有对应名称
#           - RuntimeError: 实际返回的工具集合与请求不一致（部分丢失）
#         """
#         # 参数校验
#         if not names or not isinstance(names, list):
#             raise ValueError("get_tools() 参数错误：必须提供非空的 MCP 名称列表。")

#         # 检查请求名称在配置中是否存在
#         missing_in_config = [n for n in names if n not in self.config]
#         if missing_in_config:
#             raise ValueError(f"get_tools() 参数错误：以下 MCP 名称未在配置中定义：{missing_in_config}")

#         # 构建子集配置并创建客户端
#         subset = {k: v for k, v in self.config.items() if k in names}
#         client = await self._create_client(subset)

#         # 调用 client.get_tools() 并可选设置超时
#         try:
#             if timeout is not None:
#                 tools = await asyncio.wait_for(client.get_tools(), timeout=timeout)
#             else:
#                 tools = await client.get_tools()
#         except asyncio.TimeoutError as e:
#             raise RuntimeError(f"get_tools() 超时：在 {timeout} 秒内未能获取工具。") from e
#         except Exception as e:
#             raise RuntimeError(f"get_tools() 调用 MCP 客户端失败：{e}") from e

#         # tools 应当为工具对象列表，校验返回的名字是否与请求一致（至少包含全部请求项）
#         returned_names = {getattr(t, "name", None) for t in tools}
#         # 过滤 None 名称（防御）
#         returned_names = {n for n in returned_names if n}

#         missing_tools = [n for n in names if n not in returned_names]
#         if missing_tools:
#             raise RuntimeError(
#                 f"get_tools() 结果不完整：请求的 MCP 工具 {names}，但实际只返回 {sorted(returned_names)}；缺失：{missing_tools}"
#             )

#         # 缓存并返回
#         for t in tools:
#             name = getattr(t, "name", None)
#             if name:
#                 self._tool_cache[name] = t

#         return tools

#     async def get_tool_by_name(self, name: str, timeout: Optional[float] = None) -> object:
#         """
#         按单个名称获取 MCP 工具（严格校验）。
#         - 若该工具在缓存中直接返回
#         - 若配置中不存在该名称则抛 ValueError
#         - 若 client.get_tools() 未返回该工具则抛 RuntimeError
#         """
#         if not name or not isinstance(name, str):
#             raise ValueError("get_tool_by_name() 参数错误：name 必须为非空字符串。")

#         # 缓存命中
#         if name in self._tool_cache:
#             return self._tool_cache[name]

#         if name not in self.config:
#             raise ValueError(f"get_tool_by_name() 错误：MCP 配置中不存在 '{name}'。")

#         client = await self._create_client({name: self.config[name]})

#         try:
#             if timeout is not None:
#                 tools = await asyncio.wait_for(client.get_tools(), timeout=timeout)
#             else:
#                 tools = await client.get_tools()
#         except asyncio.TimeoutError as e:
#             raise RuntimeError(f"get_tool_by_name() 超时：在 {timeout} 秒内未获取到工具 '{name}'。") from e
#         except Exception as e:
#             raise RuntimeError(f"get_tool_by_name() 调用 MCP 客户端失败：{e}") from e

#         if not tools:
#             raise RuntimeError(f"get_tool_by_name() 错误：MCP 客户端未返回任何工具用于 '{name}'。")

#         # 找到与 name 对应的工具
#         for t in tools:
#             if getattr(t, "name", None) == name:
#                 self._tool_cache[name] = t
#                 return t

#         # 如果循环结束仍未找到，则说明工具未被正确注册/返回
#         returned_names = [getattr(t, "name", None) for t in tools]
#         raise RuntimeError(
#             f"get_tool_by_name() 结果不一致：请求 '{name}'，但 MCP 客户端返回的工具为 {returned_names}。"
#         )

#     def cached_tool_names(self) -> List[str]:
#         """返回当前缓存里已加载的工具名列表（同步）"""
#         return list(self._tool_cache.keys())

#     def clear_cache(self):
#         """清空缓存（可在测试或重载配置时调用）"""
#         self._tool_cache.clear()



# import asyncio
# from core.mcp_manager import MCPManager

# async def main():
#     manager = MCPManager("config/mcp.yaml")

#     try:
#         tools = await manager.get_tools(["fetch"])
#         print("加载成功：", [t.name for t in tools])
#         print("工具缓存：", tools)
#     except Exception as e:
#         print("加载失败：", e)

# if __name__ == "__main__":
#     asyncio.run(main())