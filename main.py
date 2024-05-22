from youtube_sentiment import YouTubeSentimentAnalyzer
from news_sentiment import NewsSentimentAnalyzer
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

news_analyzer = NewsSentimentAnalyzer(NEWS_API_KEY)
youtube_analyzer = YouTubeSentimentAnalyzer(YOUTUBE_API_KEY)

file_path = './data/BTC-USD.csv'
btc_data = pd.read_csv(file_path)
btc_data['Date'] = pd.to_datetime(btc_data['Date'])
btc_prices = btc_data[btc_data['Date'].between(
    '2024-05-12', '2024-05-22')]
btc_prices = btc_prices[['Date', 'Close']]
btc_prices.set_index('Date', inplace=True)


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

    youtube_results = youtube_analyzer.display_average_sentiment_per_day(
        keyword)
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
