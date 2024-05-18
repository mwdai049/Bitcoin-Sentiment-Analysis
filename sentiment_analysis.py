import requests

# 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
# REDACTED_API


class SentimentAnalyzer:
    API_URL = "https://api-inference.huggingface.co/models/mr8488/distilroberta-finetuned-financial-news-sentiment-analysis"
    HEADERS = {"Authorization": f"Bearer REDACTED_API"}

    def query(self, payload):
        response = requests.post(
            self.API_URL, headers=self.HEADERS, json=payload)
        return response.json()

    def analyze_sentiment(self, text):
        result = self.query({"inputs": text})
        return result[0][0]
