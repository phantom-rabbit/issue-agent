from core.llm import get_llm
import json

llm = get_llm()

def generate_issue_faq(issues: list[dict], output_file: str = "data/issues_faq.json"):
    """
    使用 LLM 将每条 Issue 整理成 1-2 个 Q&A，包含解决步骤，并写入 JSON 文件
    输出格式：
    [
        {
            "question": "问题描述",
            "steps": ["步骤1", "步骤2"],
            "answer": "最终解决结果",
        }
    ]
    """
    all_faq = []

    for issue in issues:
        prompt = f"""
请根据以下 GitHub Issue 及所有评论，生成尽可能完整的 Q&A 列表，要求：
1. 每条 Q&A 包含：
- question: 提炼问题描述
- steps: 从评论中整理出真正可执行的解决步骤
- answer: 问题最终结果或结论
2. Q&A 数量根据评论内容自动生成，不超过 3 条  
3. 输出 **纯 JSON**，不要 Markdown 或多余文本

过滤掉不能实际解决问题的 Q&A，只保留能实际解决问题的 Q&A。

标题: {issue['title']}
正文: {issue['body']}
评论: {"; ".join(issue['comments'])}

输出 JSON 格式示例：
[
  {{
    "question": "Q1...",
    "steps": ["步骤1", "步骤2"],
    "answer": "A1..."
  }},
  {{
    "question": "Q2...",
    "steps": ["步骤1", "步骤2"],
    "answer": "A2..."
  }}
]
"""
        try:
            messages=[{"role": "user", "content": prompt}]
            resp = llm.invoke(messages)
            content = resp.content.strip()
            faqs = json.loads(content)
            all_faq.extend(faqs)
        except Exception as e:
            print(f"⚠️ Issue {issue['number']} 整理失败：{e}")
            continue
    
    # 去重
    all_faq = llm_deduplicate_faqs(all_faq)

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_faq, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 FAQ，共 {len(all_faq)} 条，保存至 {output_file}")
    return all_faq


def llm_deduplicate_faqs(faqs: list[dict]):
    """
    使用 LLM 去重 FAQ，合并重复问题的步骤和答案
    """

    prompt = f"""
    你是一个帮助整理 FAQ 的助手。  
我有一个 FAQ 列表，每条 FAQ 包含：

- question: 问题描述
- steps: 可执行的解决步骤列表
- answer: 最终解决结果

请帮我去掉重复或高度相似的 FAQ，保留每组相似 FAQ 的最优条目，要求：

1. 输出格式为 **纯 JSON** 数组
2. 每条 FAQ 保留原有字段：question, steps, answer
3. 不要 Markdown 包裹或多余说明

FAQ 列表：
{faqs}

    """
    messages=[{"role": "user", "content": prompt}]
    resp = llm.invoke(messages)
    content = resp.content.strip()
    print(content)
    faqs = json.loads(content)
    return faqs