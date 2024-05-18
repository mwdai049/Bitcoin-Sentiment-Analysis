from youtube_api import YouTubeAPI
from transcript import TranscriptProcessor
from sentiment_analysis import SentimentAnalyzer
import requests
import statistics


def main(company_name, channel_name):
    youtube_api = YouTubeAPI(
        'REDACTED_API', channel_name)

    try:
        def display_sentiment(score):
            n_bar = int(score*20)
            bars = "|" * n_bar
            sentiment = 'Negative      Neutral      Positive'
            print(bars)
            print(sentiment)
            return

        channel_id = youtube_api.get_channel_id()
        videos_by_day = youtube_api.get_videos_for_business_days(
            channel_id, company_name, num_days=10, videos_per_day=3)
        transcript_processor = TranscriptProcessor()
        analyzer = SentimentAnalyzer()

        for day_videos in videos_by_day:
            print(f"Processing videos for date: {day_videos['date']}")
            final_avg=0
            for video_id in day_videos['videos']:
                transcript = transcript_processor.get_transcript(video_id)
                processed_transcript = transcript_processor.preprocess_transcript(
                    transcript)
                average_score = []
                for segment in processed_transcript:
                    sentiment = analyzer.analyze_sentiment(segment)
                    average_score.append(sentiment['score'])
                if average_score:
                    calc = statistics.mean(average_score)
                    print(f"Average Score: {calc}")
                    final_avg+=calc
                    #display_sentiment(calc)
                    print("\n")
            print(final_avg/3)
            display_sentiment(final_avg/3)
    except ValueError as e:
        print(e)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    company_name = "Tesla"
    channel_name = "YahooFinance"
    main(company_name, channel_name)
