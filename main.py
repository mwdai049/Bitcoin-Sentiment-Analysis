from youtube_api import YouTubeAPI
from transcript import TranscriptProcessor
from sentiment_analysis import SentimentAnalyzer
import requests


def main(company_name, channel_name):
    youtube_api = YouTubeAPI(
        'REDACTED_API', channel_name)

    try:
        channel_id = youtube_api.get_channel_id()
        video_ids = youtube_api.get_top_videos(channel_id, company_name)
        transcript_processor = TranscriptProcessor()
        analyzer = SentimentAnalyzer()

        for video_id in video_ids:
            transcript = transcript_processor.get_transcript(video_id)
            processed_transcript = transcript_processor.preprocess_transcript(
                transcript)

            for segment in processed_transcript:
                sentiment = analyzer.analyze_sentiment(segment)
                print(f"Sentiment for segment: {segment}\n{sentiment}")

    except ValueError as e:
        print(e)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    company_name = "Google"
    channel_name = "YahooFinance"
    main(company_name, channel_name)
