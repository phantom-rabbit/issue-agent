# graphs/issue_graph.py
from langgraph.graph import StateGraph, START, END
from core.issue_state import IssueState
from agents.classifier_agent import classify_node
from agents.retriever_agent import retriever_node
from agents.reply_agent import reply_node



def build_issue_graph():
    # 创建状态图，并指定状态类型
    graph = StateGraph(IssueState)

    graph.add_node("classifier", classify_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("reply", reply_node)



    graph.add_edge(START, "classifier")
    graph.add_conditional_edges("classifier", should_retrieve)
    graph.add_edge("retriever", "reply")
    graph.add_edge("reply", END)

    return graph.compile()


def should_retrieve(state: IssueState):
    """判断是否进入retriever节点"""
    return "retriever" if state.get("need_reply", False) else END


if __name__ == "__main__":
    # 初始化状态
    state = IssueState(
        issue_body="CUDA out of memory when running model",
        issue_number=123,
        issue_title="CUDA out of memory",
        comments=[
            {"body": "Same issue as #122", "author": "user1"},
            {"body": "帮我继续解决", "author": "user2"},
        ],
    )

    graph = build_issue_graph()

    result = graph.invoke(state)
    
    print("🧩 Graph Result:", result)
