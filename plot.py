import matplotlib.pyplot as plt
import pandas as pd

youtube_data = [
    ('2024-05-10', {'positive': 4.10, 'neutral': 91.79, 'negative': 4.10}),
    ('2024-05-11', {'positive': 13.04, 'neutral': 69.78, 'negative': 17.18}),
    ('2024-05-12', {'positive': 0.0, 'neutral': 72.09, 'negative': 27.91}),
    ('2024-05-13', {'positive': 7.94, 'neutral': 77.41, 'negative': 14.65}),
    ('2024-05-14', {'positive': 2.94, 'neutral': 84.03, 'negative': 13.03}),
    ('2024-05-15', {'positive': 5.56, 'neutral': 87.92, 'negative': 6.52}),
    ('2024-05-16', {'positive': 4.59, 'neutral': 90.55, 'negative': 4.86}),
    ('2024-05-17', {'positive': 18.33, 'neutral': 73.33, 'negative': 8.33}),
    ('2024-05-18', {'positive': 18.83, 'neutral': 73.42, 'negative': 7.75}),
    ('2024-05-19', {'positive': 3.37, 'neutral': 88.50, 'negative': 8.13})
    # ('2024-05-20', {'positive': 0.0, 'neutral': 88.14, 'negative': 11.86}),
]

news_data = [
    ('2024-05-10', {'positive': 22.54, 'neutral': 60.87, 'negative': 16.59}),
    ('2024-05-11', {'positive': 14.44, 'neutral': 73.44, 'negative': 12.12}),
    ('2024-05-12', {'positive': 15.94, 'neutral': 73.43, 'negative': 10.62}),
    ('2024-05-13', {'positive': 21.15, 'neutral': 66.05, 'negative': 12.80}),
    ('2024-05-14', {'positive': 33.53, 'neutral': 49.93, 'negative': 16.55}),
    ('2024-05-15', {'positive': 25.30, 'neutral': 58.97, 'negative': 15.73}),
    ('2024-05-16', {'positive': 25.42, 'neutral': 53.67, 'negative': 20.91}),
    ('2024-05-17', {'positive': 29.80, 'neutral': 55.22, 'negative': 14.98}),
    ('2024-05-18', {'positive': 29.95, 'neutral': 56.33, 'negative': 13.71}),
    ('2024-05-19', {'positive': 30.97, 'neutral': 58.59, 'negative': 10.45})
]


stock_prices = pd.DataFrame({
    'Date': ['2024-05-10', '2024-05-11', '2024-05-12', '2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16', '2024-05-17', '2024-05-18', '2024-05-19', '2024-05-20'],
    'Close/Last': [60792.78, 60793.71, 61448.39, 62901.45, 61552.79, 66267.49, 65231.58, 67051.88, 66940.80, 66685.34, 71473.60]
    # 'Close/Last': [53.99, 56.19, 54.78, 58.82, 58.02, 59.73]
})


def plot_sentiment_and_stock_prices(news_data, youtube_data, stock_prices):
    dates = [item[0] for item in news_data]
    news_positive = [item[1]['positive'] for item in news_data]
    youtube_positive = [item[1]['positive'] for item in youtube_data]
    news_neutral = [item[1]['neutral'] for item in news_data]
    youtube_neutral = [item[1]['neutral'] for item in youtube_data]
    news_negative = [item[1]['negative'] for item in news_data]
    youtube_negative = [item[1]['negative'] for item in youtube_data]

    avg_positive = [(news + youtube) / 2 for news,
                    youtube in zip(news_positive, youtube_positive)]
    avg_neutral = [(news + youtube) / 2 for news,
                   youtube in zip(news_neutral, youtube_neutral)]
    avg_negative = [(news + youtube) / 2 for news,
                    youtube in zip(news_negative, youtube_negative)]

    stock_prices['Date'] = pd.to_datetime(stock_prices['Date'])
    stock_prices.set_index('Date', inplace=True)
    stock_prices = stock_prices.reindex(pd.to_datetime(dates)).reset_index()

    stock_dates = stock_prices['index'].dt.strftime('%Y-%m-%d')
    stock_values = stock_prices['Close/Last']

    x = range(len(dates))

    fig, axs = plt.subplots(4, 1, figsize=(14, 14), sharex=True)

    # Plot stock prices
    axs[0].plot(x, stock_values, label='Stock Prices', marker='s', color='b')
    axs[0].set_ylabel('Stock Price ($)')
    axs[0].set_title('Stock Prices')
    axs[0].legend()
    axs[0].grid(True)
    stock_min = stock_values.min()
    stock_max = stock_values.max()
    # axs[0].set_ylim(0,
    #                 stock_max + 10)

    # Plot positive sentiment
    axs[1].plot(x, news_positive, label='News Positive', marker='o', color='g')
    axs[1].plot(x, youtube_positive, label='YouTube Positive',
                marker='x', color='r')
    axs[1].plot(x, avg_positive, label='Average Positive',
                marker='D', color='m')
    axs[1].set_ylabel('Positive Sentiment (%)')
    axs[1].set_title('Positive Sentiment')
    axs[1].legend()
    axs[1].grid(True)
    # axs[1].set_ylim(bottom=0)

    # Plot neutral sentiment
    axs[2].plot(x, news_neutral, label='News Neutral', marker='o', color='g')
    axs[2].plot(x, youtube_neutral, label='YouTube Neutral',
                marker='x', color='r')
    axs[2].plot(x, avg_neutral, label='Average Neutral', marker='D', color='m')
    axs[2].set_ylabel('Neutral Sentiment (%)')
    axs[2].set_title('Neutral Sentiment')
    axs[2].legend()
    axs[2].grid(True)
    # axs[2].set_ylim(bottom=0)

    # Plot negative sentiment
    axs[3].plot(x, news_negative, label='News Negative', marker='o', color='g')
    axs[3].plot(x, youtube_negative, label='YouTube Negative',
                marker='x', color='r')
    axs[3].plot(x, avg_negative, label='Average Negative',
                marker='D', color='m')
    axs[3].set_ylabel('Negative Sentiment (%)')
    axs[3].set_title('Negative Sentiment')
    axs[3].legend()
    axs[3].grid(True)
    # axs[3].set_ylim(bottom=0)

    plt.xticks(x, dates, rotation='vertical')
    plt.xlabel('Date')
    plt.tight_layout()
    plt.show()


plot_sentiment_and_stock_prices(news_data, youtube_data, stock_prices)
