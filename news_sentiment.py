import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta


class NewsSentimentAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.analyzer = SentimentIntensityAnalyzer()

    def get_articles_for_keyword(self, keyword, published_after, published_before, max_results=10):
        url = f"https://newsapi.org/v2/everything?q={keyword}&from={published_after}&to={published_before}&sortBy=popularity&pageSize={max_results}&apiKey={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return []

        articles = response.json().get('articles', [])
        return articles[:10]  # Restrict to top 3 articles

    def analyze_sentiment(self, text):
        sentiment_scores = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        highest_negative_sentiment = -1
        top_negative_snippet = ""

        lines = text.split('.')
        for line in lines:
            sentiment = self.analyzer.polarity_scores(line)
            negative_score = sentiment['neg']

            if sentiment['compound'] >= 0.05:
                sentiment_scores['positive'] += 1
            elif sentiment['compound'] <= -0.05:
                sentiment_scores['negative'] += 1
            else:
                sentiment_scores['neutral'] += 1

            if negative_score > highest_negative_sentiment:
                highest_negative_sentiment = negative_score
                top_negative_snippet = line

        total = sum(sentiment_scores.values())
        if total > 0:
            for key in sentiment_scores:
                sentiment_scores[key] = (sentiment_scores[key] / total) * 100

        return sentiment_scores, top_negative_snippet

    def calculate_average_sentiment(self, articles):
        sentiment_totals = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        count = len(articles)
        article_sentiments = []

        for article in articles:
            text = article['content'] or article['description'] or ""
            sentiment, top_negative_snippet = self.analyze_sentiment(text)
            article_sentiments.append({
                'title': article['title'],
                'sentiment': sentiment,
                'top_snippet': top_negative_snippet
            })
            for key in sentiment:
                sentiment_totals[key] += sentiment[key]

        if count > 0:
            for key in sentiment_totals:
                sentiment_totals[key] /= count

        return sentiment_totals, article_sentiments

    def display_average_sentiment_per_day(self, keyword):
        today = datetime.utcnow()
        days = [today - timedelta(days=i) for i in range(10)]

        for day in days:
            published_after = day.replace(
                hour=0, minute=0, second=0).isoformat("T") + "Z"
            published_before = (day + timedelta(days=1)).replace(hour=0,
                                                                 minute=0, second=0).isoformat("T") + "Z"

            articles = self.get_articles_for_keyword(
                keyword, published_after, published_before, max_results=10)
            if articles:
                average_sentiment, article_sentiments = self.calculate_average_sentiment(
                    articles)
                print(f"Date: {day.strftime('%Y-%m-%d')}")
                print(f"Average Sentiment: {average_sentiment}")
                print("Top Articles and Snippets:")
                for article in article_sentiments:
                    print(f"  Title: {article['title']}")
                    print(f"  Sentiment: {article['sentiment']}")
                    print(f"  Top Negative Snippet: {article['top_snippet']}")
                    print("----------")
            else:
                print(f"Date: {day.strftime('%Y-%m-%d')}")
                print("No suitable articles found.")
                print("----------")
