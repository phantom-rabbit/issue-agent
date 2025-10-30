
from typing import List, Optional, TypedDict
from langchain_core.documents import Document


class IssueState(TypedDict):
    issue_url: str
    issue_number: int
    issue_title: str
    issue_body: str
    comments: List[str]
    need_reply: bool
    retrieved_docs: Optional[List[Document]]
    reply_text: Optional[str]
    category: Optional[str]
    reason: Optional[str]