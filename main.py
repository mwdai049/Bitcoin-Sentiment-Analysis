from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import isodate
from datetime import datetime, timedelta
from transformers import pipeline
from news_sentiment import NewsSentimentAnalyzer
import os

API_KEY = 'REDACTED_API'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
TRANSCRIPTS_DIR = 'transcripts'

youtube = build(YOUTUBE_API_SERVICE_NAME,
                YOUTUBE_API_VERSION, developerKey=API_KEY)

classifier = pipeline('sentiment-analysis', model='ProsusAI/finbert')


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

        if len(videos) == 3:
            break

    return videos


def analyze_sentiment(transcript):
    sentiment_scores = {'positive': 0, 'neutral': 0, 'negative': 0}
    highest_negative_sentiment = -1
    top_negative_snippet = ""

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
        else:
            sentiment_scores['neutral'] += 1

    total = sum(sentiment_scores.values())
    if total > 0:
        for key in sentiment_scores:
            sentiment_scores[key] = (sentiment_scores[key] / total) * 100

    return sentiment_scores, top_negative_snippet


def calculate_average_sentiment(videos):
    sentiment_totals = {'positive': 0, 'neutral': 0, 'negative': 0}
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


def save_transcripts(videos, date):
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.makedirs(TRANSCRIPTS_DIR)

    for video in videos:
        file_path = os.path.join(
            TRANSCRIPTS_DIR, f"{date}_{video['video_id']}.txt")
        with open(file_path, 'w') as file:
            for entry in video['transcript']:
                file.write(entry['text'] + '\n')


def get_business_days(start_date, num_days):
    business_days = []
    while len(business_days) < num_days:
        if start_date.weekday() < 5:
            business_days.append(start_date)
        start_date -= timedelta(days=1)
    return business_days


def display_average_sentiment_per_day(keyword):
    today = datetime.utcnow()
    days = [today - timedelta(days=i) for i in range(11)]

    for day in days:
        published_after = day.replace(
            hour=0, minute=0, second=0).isoformat("T") + "Z"
        published_before = (day + timedelta(days=1)).replace(hour=0,
                                                             minute=0, second=0).isoformat("T") + "Z"

        videos = get_videos_for_keyword(
            keyword, published_after, published_before, max_results=10)
        top_videos = videos[:3]

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
                print("----------")
        else:
            print(f"Date: {day.strftime('%Y-%m-%d')}")
            print("No suitable videos found.")
            print("----------")


def save_transcript(video_id, transcript):
    if not os.path.exists(TRANSCRIPTS_DIR):
        os.makedirs(TRANSCRIPTS_DIR)
    file_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}.txt")
    with open(file_path, 'w') as file:
        for entry in transcript:
            file.write(entry['text'] + '\n')


def get_top_video_for_keyword(keyword, max_results=1):
    request = youtube.search().list(
        q=keyword,
        part='id,snippet',
        type='video',
        maxResults=max_results,
        publishedAfter=datetime.utcnow().replace(
            hour=0, minute=0, second=0).isoformat("T") + "Z",
        order='viewCount'
    )
    response = request.execute()

    if not response['items']:
        return None

    top_video = response['items'][0]
    video_id = top_video['id']['videoId']
    return {
        'video_id': video_id,
        'title': top_video['snippet']['title']
    }


def test_single_video_by_keyword(keyword):
    video_info = get_top_video_for_keyword(keyword)
    if not video_info:
        print("No video found for the given keyword.")
        return

    video_id = video_info['video_id']
    title = video_info['title']
    print(f"Testing video: {title} (ID: {video_id})")

    video_details = get_video_details(video_id)
    if not video_details or video_details['duration'] > 1800:
        print("Video is either too long or details could not be fetched.")
        return

    transcript = get_video_transcript(video_id)
    if transcript is None:
        print("Transcript not available.")
        return

    save_transcript(video_id, transcript)

    sentiment, top_negative_snippet = analyze_sentiment(transcript)
    print(f"Sentiment Scores: {sentiment}")
    print(f"Top Negative Snippet: {top_negative_snippet}")


if __name__ == "__main__":
    keyword = "Bitcoin stock"
    # display_average_sentiment_per_day(keyword)
    # test_single_video_by_keyword(keyword)

    news_analyzer = NewsSentimentAnalyzer('367a29799166461e9f1f99cf648d99c2')
    news_analyzer.display_average_sentiment_per_day(keyword)
    # news_analyzer.test_single_article_by_keyword(keyword)
