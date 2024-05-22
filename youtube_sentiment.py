from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import isodate
from datetime import datetime, timedelta
from transformers import pipeline
import os

TRANSCRIPTS_DIR = 'transcripts'


class YouTubeSentimentAnalyzer:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.classifier = pipeline(
            'sentiment-analysis', model='ProsusAI/finbert')

    def get_video_details(self, video_id):
        request = self.youtube.videos().list(part="contentDetails", id=video_id)
        response = request.execute()
        if not response['items']:
            return None
        content_details = response['items'][0]['contentDetails']
        duration = isodate.parse_duration(
            content_details['duration']).total_seconds()
        return {'duration': duration}

    def get_video_transcript(self, video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except (TranscriptsDisabled, NoTranscriptFound):
            return None

    def get_videos_for_keyword(self, keyword, published_after, published_before, max_results=10):
        request = self.youtube.search().list(
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
            video_details = self.get_video_details(video_id)

            if not video_details or video_details['duration'] > 1800:
                continue

            transcript = self.get_video_transcript(video_id)
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

    def analyze_sentiment(self, transcript):
        sentiment_scores = {'positive': 0, 'neutral': 0, 'negative': 0}
        highest_negative_sentiment = -1
        top_negative_snippet = ""
        top_negative_time = ""

        lines = [entry['text'] for entry in transcript]
        for i in range(0, len(lines), 10):
            segment = ' '.join(lines[i:i + 10])
            result = self.classifier(segment)[0]
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

    def calculate_average_sentiment(self, videos):
        sentiment_totals = {'positive': 0, 'neutral': 0, 'negative': 0}
        count = len(videos)
        video_sentiments = []

        for video in videos:
            sentiment, top_negative_snippet, top_negative_time = self.analyze_sentiment(
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

    def save_transcripts(self, videos, date):
        if not os.path.exists(TRANSCRIPTS_DIR):
            os.makedirs(TRANSCRIPTS_DIR)
        for video in videos:
            file_path = os.path.join(
                TRANSCRIPTS_DIR, f"{date}_{video['video_id']}.txt")
            with open(file_path, 'w') as file:
                for entry in video['transcript']:
                    file.write(entry['text'] + '\n')

    def display_average_sentiment_per_day(self, keyword):
        today = datetime.utcnow()
        days = [today - timedelta(days=i) for i in range(11)]
        youtube_results = []

        for day in days:
            published_after = day.replace(
                hour=0, minute=0, second=0).isoformat("T") + "Z"
            published_before = (day + timedelta(days=1)).replace(hour=0,
                                                                 minute=0, second=0).isoformat("T") + "Z"
            videos = self.get_videos_for_keyword(
                keyword, published_after, published_before, max_results=10)
            top_videos = videos[:5]

            if top_videos:
                self.save_transcripts(top_videos, day)
                average_sentiment, video_sentiments = self.calculate_average_sentiment(
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
