from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import isodate
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_sentiment import NewsSentimentAnalyzer


# Replace with your API key
API_KEY = 'REDACTED_API'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Initialize YouTube API client
youtube = build(YOUTUBE_API_SERVICE_NAME,
                YOUTUBE_API_VERSION, developerKey=API_KEY)

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()


def get_video_details(video_id):
    request = youtube.videos().list(
        part="contentDetails",
        id=video_id
    )
    response = request.execute()
    if not response['items']:
        return None
    content_details = response['items'][0]['contentDetails']
    duration = isodate.parse_duration(
        content_details['duration']).total_seconds()
    return {
        'duration': duration
    }


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
    for item in response['items']:
        video_id = item['id']['videoId']
        video_details = get_video_details(video_id)

        # 1800 seconds = 30 minutes
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

    return videos


def analyze_sentiment(transcript):
    sentiment_scores = {
        'positive': 0,
        'neutral': 0,
        'negative': 0
    }
    highest_negative_sentiment = -1
    top_negative_snippet = ""

    for entry in transcript:
        text = entry['text']
        sentiment = analyzer.polarity_scores(text)
        negative_score = sentiment['neg']

        if sentiment['compound'] >= 0.05:
            sentiment_scores['positive'] += 1
        elif sentiment['compound'] <= -0.05:
            sentiment_scores['negative'] += 1
        else:
            sentiment_scores['neutral'] += 1

        if negative_score > highest_negative_sentiment:
            highest_negative_sentiment = negative_score
            top_negative_snippet = text

    total = sum(sentiment_scores.values())
    if total > 0:
        for key in sentiment_scores:
            sentiment_scores[key] = (sentiment_scores[key] / total) * 100

    return sentiment_scores, top_negative_snippet


def calculate_average_sentiment(videos):
    sentiment_totals = {
        'positive': 0,
        'neutral': 0,
        'negative': 0
    }
    count = len(videos)
    video_sentiments = []

    for video in videos:
        sentiment, top_negative_snippet = analyze_sentiment(
            video['transcript'])
        video_sentiments.append({
            'title': video['title'],
            'sentiment': sentiment,
            'top_snippet': top_negative_snippet
        })
        for key in sentiment:
            sentiment_totals[key] += sentiment[key]

    if count > 0:
        for key in sentiment_totals:
            sentiment_totals[key] /= count

    return sentiment_totals, video_sentiments


def display_average_sentiment_per_day(keyword):
    today = datetime.utcnow()
    days = [today - timedelta(days=i) for i in range(10)]

    for day in days:
        published_after = day.replace(
            hour=0, minute=0, second=0).isoformat("T") + "Z"
        published_before = (day + timedelta(days=1)).replace(hour=0,
                                                             minute=0, second=0).isoformat("T") + "Z"

        videos = get_videos_for_keyword(
            keyword, published_after, published_before, max_results=10)
        top_videos = videos[:3]  # Get the top 3 videos

        if top_videos:
            average_sentiment, video_sentiments = calculate_average_sentiment(
                top_videos)
            print(f"Date: {day.strftime('%Y-%m-%d')}")
            print(f"Average Sentiment: {average_sentiment}")
            print("Top Videos and Snippets:")
            for video in video_sentiments:
                print(f"  Title: {video['title']}")
                print(f"  Sentiment: {video['sentiment']}")
                print(f"  Top Negative Snippet: {video['top_snippet']}")
                print("----------")
        else:
            print(f"Date: {day.strftime('%Y-%m-%d')}")
            print("No suitable videos found.")
            print("----------")


# if __name__ == "__main__":
    # keyword = "Apple stock"
    # display_average_sentiment_per_day(keyword)

    # analyzer = NewsSentimentAnalyzer('REDACTED_API')
    # analyzer.display_average_sentiment_per_day(keyword)
