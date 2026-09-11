import re


class TextEmbedder:
    """
    โมดูลสำหรับจัดการประมวลผลข้อความ (Embedding & Tokenization)
    ทำงานแบบ Offline 100% ตามข้อกำหนดของ Iteration 2
    """
    def __init__(self):
        pass

    def tokenize(self, text: str) -> list[str]:
        """
        ตัดคำและทำความสะอาดข้อความเพื่อส่งให้ BM25 Retriever
        """
        if not text:
            return []
        # แปลงเป็นพิมพ์เล็กและดึงมาเฉพาะตัวอักษร/ตัวเลข
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def embed(self, text: str) -> list[float]:
        """
        Placeholder สำหรับ Contract ของทีม
        รองรับการเปลี่ยนไปใช้ Dense Model (เช่น SentenceTransformers) ในอนาคต
        """
        return []
