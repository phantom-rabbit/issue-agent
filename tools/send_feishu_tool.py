#!/usr/bin/env python3
"""
MCP 工具：飞书消息发送器

此工具用于通过飞书 Webhook 发送消息通知
支持作为独立脚本运行或作为 MCP 工具被调用
"""

import asyncio
import json
import aiohttp
import sys
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('feishu-mcp-tool')


class FeishuTool:
    """
    飞书消息发送工具类
    实现 MCP 标准的工具接口
    """
    
    async def send_feishu_message(self, content: str, webhook_url: str) -> dict:
        """
        发送消息到飞书
        
        Args:
            content: 要发送的消息内容
            webhook_url: 飞书机器人的 Webhook URL
            
        Returns:
            dict: 包含发送结果的字典
        """
        try:
            # 验证输入参数
            if not content or not webhook_url:
                return {
                    "success": False,
                    "error": "Missing required parameters: content and webhook_url are required"
                }
            
            # 构建请求体
            payload = {
                "msg_type": "text",
                "content": {"text": content}
            }
            
            logger.info(f"Preparing to send message to Feishu, content length: {len(content)} chars")
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=30
                ) as resp:
                    
                    status = resp.status
                    text = await resp.text()
                    
                    try:
                        # 尝试解析 JSON 响应
                        result = json.loads(text)
                        
                        # 根据状态码和响应内容判断是否成功
                        if status == 200 and result.get("code") == 0:
                            logger.info("Message sent to Feishu successfully")
                            return {
                                "success": True,
                                "data": result
                            }
                        else:
                            logger.error(f"Failed to send message: status {status}, response {result}")
                            return {
                                "success": False,
                                "status_code": status,
                                "error": result.get("msg", "Unknown error"),
                                "data": result
                            }
                    
                    except json.JSONDecodeError:
                        # 处理非 JSON 响应
                        logger.error(f"Invalid JSON response: {text}")
                        return {
                            "success": False,
                            "status_code": status,
                            "error": "Invalid JSON response",
                            "raw_response": text
                        }
        
        except asyncio.TimeoutError:
            logger.error("Request to Feishu timed out")
            return {
                "success": False,
                "error": "Timeout when sending message"
            }
        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {str(e)}")
            return {
                "success": False,
                "error": f"HTTP client error: {str(e)}"
            }
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def process_mcp_request(self) -> None:
        """
        处理 MCP 格式的请求
        从标准输入读取 JSON 请求，调用工具，然后将结果输出到标准输出
        """
        try:
            # 从标准输入读取请求
            input_data = sys.stdin.read().strip()
            
            if not input_data:
                logger.error("Empty input received")
                sys.stdout.write(json.dumps({
                    "success": False,
                    "error": "No input data provided"
                }))
                return
            
            # 解析 JSON 请求
            request = json.loads(input_data)
            
            # 提取参数
            params = request.get("params", {})
            content = params.get("content")
            webhook_url = params.get("webhook_url")
            
            # 如果没有提供 webhook_url，可以尝试从环境变量获取默认值
            if not webhook_url:
                webhook_url = os.getenv("FEISHU_WEBHOOK_URL")
                if not webhook_url:
                    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/874bf562-1ee7-4143-bc15-2481e42cff03"
            
            # 调用工具函数
            result = await self.send_feishu_message(content, webhook_url)
            
            # 输出结果到标准输出
            sys.stdout.write(json.dumps(result))
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {str(e)}")
            sys.stdout.write(json.dumps({
                "success": False,
                "error": f"Invalid JSON input: {str(e)}"
            }))
        
        except Exception as e:
            logger.error(f"Error processing MCP request: {str(e)}")
            sys.stdout.write(json.dumps({
                "success": False,
                "error": f"Internal error: {str(e)}"
            }))


# 创建工具实例
feishu_tool = FeishuTool()


# 公开的工具函数，用于直接调用
def send_feishu(content: str, webhook_url: str = None) -> dict:
    """
    同步版本的飞书消息发送函数
    
    Args:
        content: 消息内容
        webhook_url: Webhook URL，如果不提供则使用默认值
        
    Returns:
        dict: 发送结果
    """
    if not webhook_url:
        webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/874bf562-1ee7-4143-bc15-2481e42cff03")
    
    return asyncio.run(feishu_tool.send_feishu_message(content, webhook_url))


# 命令行入口
if __name__ == "__main__":
    """
    命令行入口，用于 MCP 标准调用
    当作为脚本运行时，处理 MCP 格式的输入输出
    """
    try:
        # 运行 MCP 请求处理
        asyncio.run(feishu_tool.process_mcp_request())
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1)
