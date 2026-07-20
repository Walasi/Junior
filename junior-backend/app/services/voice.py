class VoiceService:
    @staticmethod
    def extract_embedding(audio_bytes: bytes) -> list:
        return [0.0] * 192

    @staticmethod
    def compare_embeddings(emb1: list, emb2: list) -> float:
        return 0.8