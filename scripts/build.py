from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = "BAAI/bge-small-zh"):
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str):
        return self.model.encode(text).tolist()  # 转为 list

    def embed_documents(self, texts: list[str]):
        return self.model.encode(texts).tolist()  # 转为 list


def build_vector_db(json_file: str, persist_dir: str):
    """
    从 FAQ JSON 文件生成向量数据库并存储
    """
    # 读取 JSON
    with open(json_file, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    # 构建 Document 对象
    docs = [
        Document(
            page_content=f"Q: {i['question']}\nSteps:\n" + "\n".join(i.get("steps", [])) + f"\nA: {i.get('answer','')}",
            metadata={"title": i.get("question", "")}
        )
        for i in faqs
    ]

    # 文本切分
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)
    print(f"✂️ 已分割为 {len(split_docs)} 条文本块，开始生成向量...")

    # 提取文本和元数据
    texts = [d.page_content for d in split_docs]
    metadatas = [d.metadata for d in split_docs]

    # 初始化嵌入模型
    embeddings = LocalEmbeddings("BAAI/bge-small-zh")

    # 创建 Chroma 向量数据库并批量添加
    db = Chroma(
        collection_name="issues",
        persist_directory=persist_dir,
        embedding_function=embeddings
    )
    db.add_texts(texts, metadatas=metadatas)

    print(f"✅ 向量数据库已保存至：{persist_dir}")


chroma_db_path = "data/chroma_db"
if __name__ == "__main__":
    build_vector_db("data/issues_faq.json", chroma_db_path)
