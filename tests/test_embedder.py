from src.rag.embedder import TextEmbedder

def test_embedder_tokenize():
    embedder = TextEmbedder()
    # ทดสอบการทำตัวพิมพ์เล็กและตัดสัญลักษณ์
    tokens = embedder.tokenize("Brute-Force & Password 123!")
    assert tokens == ["brute", "force", "password", "123"]

def test_embedder_empty_input():
    embedder = TextEmbedder()
    assert embedder.tokenize("") == []
    assert embedder.tokenize(None) == []

def test_embedder_mock_vector():
    embedder = TextEmbedder()
    # ทดสอบว่าฟังก์ชัน embed ไม่พังและคืนค่าโครงสร้างที่ถูกต้อง
    assert isinstance(embedder.embed("test"), list)