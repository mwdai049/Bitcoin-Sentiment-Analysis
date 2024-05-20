from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import isodate
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class YouTubeSentimentAnalyzer:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.analyzer = SentimentIntensityAnalyzer()

    def get_video_details(self, video_id):
        request = self.youtube.videos().list(
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
        for item in response['items']:
            video_id = item['id']['videoId']
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

        return videos

    def analyze_sentiment(self, transcript):
        sentiment_scores = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        highest_negative_sentiment = -1
        top_negative_snippet = ""

        for entry in transcript:
            text = entry['text']
            sentiment = self.analyzer.polarity_scores(text)
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

    def calculate_average_sentiment(self, videos):
        sentiment_totals = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        count = len(videos)
        video_sentiments = []

        for video in videos:
            sentiment, top_negative_snippet = self.analyze_sentiment(
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

    def get_average_sentiment_per_day(self, keyword):
        today = datetime.utcnow()
        days = [today - timedelta(days=i) for i in range(10)]
        daily_sentiments = []

        for day in days:
            published_after = day.replace(
                hour=0, minute=0, second=0).isoformat("T") + "Z"
            published_before = (day + timedelta(days=1)).replace(hour=0,
                                                                 minute=0, second=0).isoformat("T") + "Z"

            videos = self.get_videos_for_keyword(
                keyword, published_after, published_before, max_results=10)
            top_videos = videos[:10]

            if top_videos:
                average_sentiment, video_sentiments = self.calculate_average_sentiment(
                    top_videos)
                daily_sentiments.append(
                    (day.strftime('%Y-%m-%d'), average_sentiment))
            else:
                daily_sentiments.append(
                    (day.strftime('%Y-%m-%d'), {'positive': 0, 'neutral': 0, 'negative': 0}))

        return daily_sentiments
