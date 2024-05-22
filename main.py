from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import isodate
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
from transformers import pipeline
from news_sentiment import NewsSentimentAnalyzer
import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
TRANSCRIPTS_DIR = 'transcripts'

youtube = build(YOUTUBE_API_SERVICE_NAME,
                YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

classifier = pipeline('sentiment-analysis', model='ProsusAI/finbert')
news_analyzer = NewsSentimentAnalyzer(NEWS_API_KEY)

file_path = './data/BTC-USD.csv'
btc_data = pd.read_csv(file_path)
btc_data['Date'] = pd.to_datetime(btc_data['Date'])
btc_prices = btc_data[btc_data['Date'].between(
    '2024-05-12', '2024-05-22')]
btc_prices = btc_prices[['Date', 'Close']]
btc_prices.set_index('Date', inplace=True)


def get_video_details(video_id):
    request = youtube.videos().list(part="contentDetails", id=video_id)
    response = request.execute()
    if not response['items']:
        return None
    content_details = response['items'][0]['contentDetails']
    duration = isodate.parse_duration(
        content_details['duration']).total_seconds()
    return {'duration': duration}


def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except (TranscriptsDisabled, NoTranscriptFound):
        return None


def get_videos_for_keyword(keyword, published_after, published_before, max_results=10):
    request = youtube.search().list(
        q=keyword,
        part='id,snippet',
        type='video',
        maxResults=max_results,
        order='viewCount',
        publishedAfter=published_after,
        publishedBefore=published_before
    )
    response = request.execute()

    videos = []
    first_keyword = keyword.split()[0].lower()

    for item in response['items']:
        video_id = item['id']['videoId']
        title = item['snippet']['title'].lower()

        if first_keyword not in title:
            continue
        video_details = get_video_details(video_id)

        if not video_details or video_details['duration'] > 1800:
            continue

        transcript = get_video_transcript(video_id)
        if transcript is None:
            continue

        videos.append({
            'video_id': video_id,
            'title': item['snippet']['title'],
            'transcript': transcript
        })

        if len(videos) == 5:
            break

    return videos


def analyze_sentiment(transcript):
    sentiment_scores = {'positive': 0, 'neutral': 0, 'negative': 0}
    highest_negative_sentiment = -1
    top_negative_snippet = ""
    top_negative_timestamp = ""
    top_negative_time = ""

    lines = [entry['text'] for entry in transcript]
    for i in range(0, len(lines), 10):
        segment = ' '.join(lines[i:i + 10])
        result = classifier(segment)[0]
        label = result['label']
        score = result['score']

        if label == 'positive':
            sentiment_scores['positive'] += 1.5
        elif label == 'negative':
            sentiment_scores['negative'] += 1.5
            if score > highest_negative_sentiment:
                highest_negative_sentiment = score
                top_negative_snippet = segment
                top_negative_time = transcript[i]['start']
        else:
            sentiment_scores['neutral'] += 1

    total = sum(sentiment_scores.values())
    if total > 0:
        for key in sentiment_scores:
            sentiment_scores[key] = (sentiment_scores[key] / total) * 100

    if top_negative_time:
        minutes = int(top_negative_time // 60)
        seconds = int(top_negative_time % 60)
        top_negative_time = f"{minutes}:{seconds:02d}"

    return sentiment_scores, top_negative_snippet, top_negative_time


def calculate_average_sentiment(videos):
    sentiment_totals = {'positive': 0, 'neutral': 0, 'negative': 0}
    count = len(videos)
    video_sentiments = []

    for video in videos:
        sentiment, top_negative_snippet, top_negative_time = analyze_sentiment(
            video['transcript'])
        video_sentiments.append({
            'title': video['title'],
            'sentiment': sentiment,
            'top_snippet': top_negative_snippet,
            'top_negative_timestamp': top_negative_time
        })
        for key in sentiment:
            sentiment_totals[key] += sentiment[key]

    if count > 0:
        for key in sentiment_totals:
            sentiment_totals[key] /= count

    return sentiment_totals, video_sentiments


def save_transcripts(videos, date):
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.makedirs(TRANSCRIPTS_DIR)
    for video in videos:
        file_path = os.path.join(
            TRANSCRIPTS_DIR, f"{date}_{video['video_id']}.txt")
        with open(file_path, 'w') as file:
            for entry in video['transcript']:
                file.write(entry['text'] + '\n')


def display_average_sentiment_per_day(keyword):
    today = datetime.utcnow()
    days = [today - timedelta(days=i) for i in range(11)]
    youtube_results = []

    for day in days:
        published_after = day.replace(
            hour=0, minute=0, second=0).isoformat("T") + "Z"
        published_before = (day + timedelta(days=1)).replace(hour=0,
                                                             minute=0, second=0).isoformat("T") + "Z"
        videos = get_videos_for_keyword(
            keyword, published_after, published_before, max_results=10)
        top_videos = videos[:5]

        if top_videos:
            save_transcripts(top_videos, day)
            average_sentiment, video_sentiments = calculate_average_sentiment(
                top_videos)
            print(f"Date: {day.strftime('%Y-%m-%d')}")
            print(f"Average Sentiment: {average_sentiment}")
            print("Top Videos and Snippets:")
            for video in video_sentiments:
                print(f"  Title: {video['title']}")
                print(f"  Sentiment: {video['sentiment']}")
                print(f"  Top Negative Snippet: {video['top_snippet']}")
                print(
                    f"  Timestamp: {video['top_negative_timestamp']}")
                print("----------")

            youtube_results.append({
                'date': day.strftime('%Y-%m-%d'),
                'average_sentiment': average_sentiment,
                'top_videos': video_sentiments
            })

    return youtube_results


def plot_sentiment_and_stock_prices(news_data, youtube_data, stock_prices):
    dates = stock_prices.index.strftime('%Y-%m-%d')
    news_positive = [float(item['average_sentiment']['positive'])
                     for item in news_data]
    youtube_positive = [float(item['average_sentiment']['positive'])
                        for item in youtube_data]
    news_neutral = [float(item['average_sentiment']['neutral'])
                    for item in news_data]
    youtube_neutral = [float(item['average_sentiment']['neutral'])
                       for item in youtube_data]
    news_negative = [float(item['average_sentiment']['negative'])
                     for item in news_data]
    youtube_negative = [float(item['average_sentiment']['negative'])
                        for item in youtube_data]

    avg_positive = [(news + youtube) / 2 for news,
                    youtube in zip(news_positive, youtube_positive)]
    avg_neutral = [(news + youtube) / 2 for news,
                   youtube in zip(news_neutral, youtube_neutral)]
    avg_negative = [(news + youtube) / 2 for news,
                    youtube in zip(news_negative, youtube_negative)]

    stock_values = stock_prices['Close']

    x = range(len(dates))

    fig, axs = plt.subplots(4, 1, figsize=(14, 14), sharex=True)

    axs[0].plot(x, stock_values, label='BTC-USD',
                marker='s', color='b')
    axs[0].set_ylabel('BTC-USD')
    axs[0].set_title('Bitcoin USD (BTC-USD)')
    axs[0].legend()
    axs[0].grid(True)
    stock_min = stock_values.min()
    stock_max = stock_values.max()

    axs[1].plot(x, news_positive, label='News Positive', marker='o', color='g')
    axs[1].plot(x, youtube_positive, label='YouTube Positive',
                marker='x', color='r')
    axs[1].plot(x, avg_positive, label='Average Positive',
                marker='D', color='m')
    axs[1].set_ylabel('Positive Sentiment (%)')
    axs[1].set_title('Positive Sentiment')
    axs[1].legend()
    axs[1].grid(True)

    axs[2].plot(x, news_neutral, label='News Neutral', marker='o', color='g')
    axs[2].plot(x, youtube_neutral, label='YouTube Neutral',
                marker='x', color='r')
    axs[2].plot(x, avg_neutral, label='Average Neutral', marker='D', color='m')
    axs[2].set_ylabel('Neutral Sentiment (%)')
    axs[2].set_title('Neutral Sentiment')
    axs[2].legend()
    axs[2].grid(True)

    axs[3].plot(x, news_negative, label='News Negative', marker='o', color='g')
    axs[3].plot(x, youtube_negative, label='YouTube Negative',
                marker='x', color='r')
    axs[3].plot(x, avg_negative, label='Average Negative',
                marker='D', color='m')
    axs[3].set_ylabel('Negative Sentiment (%)')
    axs[3].set_title('Negative Sentiment')
    axs[3].legend()
    axs[3].grid(True)

    plt.xticks(x, dates, rotation='vertical')
    plt.xlabel('Date')
    plt.tight_layout()
    plt.show()


def main():
    keyword = "Bitcoin stock"

    youtube_results = display_average_sentiment_per_day(keyword)
    news_results = news_analyzer.display_average_sentiment_per_day(keyword)

    summary = []
    for date in btc_prices.index.strftime('%Y-%m-%d'):
        stock_price = btc_prices.loc[date, 'Close'] if date in btc_prices.index.strftime(
            '%Y-%m-%d') else 'N/A'
        youtube_sentiment = next(
            (item['average_sentiment'] for item in youtube_results if item['date'] == date), None)
        news_sentiment = next((item['average_sentiment']
                              for item in news_results if item['date'] == date), None)

        summary.append({
            'date': date,
            'close/last': stock_price,
            'youtube_positive_sentiment': youtube_sentiment['positive'] if youtube_sentiment else 'N/A',
            'news_positive_sentiment': news_sentiment['positive'] if news_sentiment else 'N/A',
            'youtube_neutral_sentiment': youtube_sentiment['neutral'] if youtube_sentiment else 'N/A',
            'news_neutral_sentiment': news_sentiment['neutral'] if news_sentiment else 'N/A',
            'youtube_negative_sentiment': youtube_sentiment['negative'] if youtube_sentiment else 'N/A',
            'news_negative_sentiment': news_sentiment['negative'] if news_sentiment else 'N/A'
        })

    print("Summary:")
    for entry in summary:
        print(entry)

    plot_sentiment_and_stock_prices(
        news_results, youtube_results, btc_prices)


if __name__ == "__main__":
    main()
