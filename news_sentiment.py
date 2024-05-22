import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from datetime import datetime, timedelta


class NewsSentimentAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.classifier = pipeline(
            'sentiment-analysis', model='ProsusAI/finbert')

    def get_articles_for_keyword(self, keyword, published_after, published_before, max_results=10):
        url = f"https://newsapi.org/v2/everything?q={keyword}&from={published_after}&to={published_before}&sortBy=popularity&pageSize={max_results}&apiKey={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            return []

        articles = response.json().get('articles', [])
        valid_articles = []

        for article in articles[:max_results]:
            full_text = self.fetch_full_article(article['url'])
            if full_text:
                article['full_text'] = full_text
                valid_articles.append(article)
                if len(valid_articles) >= 5:
                    break

        return valid_articles

    def fetch_full_article(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                full_text = ' '.join([para.get_text() for para in paragraphs])
                return full_text
        except Exception as e:
            print(f"Error fetching full article: {e}")
        return ""

    def analyze_sentiment(self, text):
        sentiment_scores = {'positive': 0, 'neutral': 0, 'negative': 0}
        highest_negative_sentiment = -1
        top_negative_snippet = ""

        lines = text.split('.')
        for line in lines:
            if not line.strip():
                continue
            result = self.classifier(line)[0]
            label = result['label']
            score = result['score']

            if label == 'positive':
                sentiment_scores['positive'] += 1.5
            elif label == 'negative':
                sentiment_scores['negative'] += 1.5
                if score > highest_negative_sentiment:
                    highest_negative_sentiment = score
                    top_negative_snippet = line
            else:
                sentiment_scores['neutral'] += 1

        total = sum(sentiment_scores.values())
        if total > 0:
            for key in sentiment_scores:
                sentiment_scores[key] = (sentiment_scores[key] / total) * 100

        return sentiment_scores, top_negative_snippet

    def calculate_average_sentiment(self, articles):
        sentiment_totals = {'positive': 0, 'neutral': 0, 'negative': 0}
        count = len(articles)
        article_sentiments = []

        for article in articles:
            sentiment, top_negative_snippet = self.analyze_sentiment(
                article['full_text'])
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
        days = [today - timedelta(days=i) for i in range(11)]
        news_results = []

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
                news_results.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'average_sentiment': average_sentiment,
                    'top_articles': article_sentiments
                })
            else:
                print(f"Date: {day.strftime('%Y-%m-%d')}")
                print("No suitable articles found.")
                news_results.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'average_sentiment': {'positive': 0, 'neutral': 0, 'negative': 0},
                })
                print("----------")

        return news_results

    def test_single_article_by_keyword(self, keyword):
        today = datetime.utcnow()
        published_after = (today - timedelta(days=1)).replace(
            hour=0, minute=0, second=0).isoformat("T") + "Z"
        published_before = today.replace(
            hour=0, minute=0, second=0).isoformat("T") + "Z"

        articles = self.get_articles_for_keyword(
            keyword, published_after, published_before, max_results=1)
        if articles:
            article = articles[0]
            full_text = self.fetch_full_article(article['url'])
            if not full_text:
                print("No suitable articles found.")
                return
            sentiment, top_negative_snippet = self.analyze_sentiment(full_text)
            print(f"Title: {article['title']}")
            print(f"Sentiment: {sentiment}")
            print(f"Top Negative Snippet: {top_negative_snippet}")
        else:
            print("No suitable articles found.")
