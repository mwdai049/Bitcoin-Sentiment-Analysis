import matplotlib.pyplot as plt
import pandas as pd

# Hardcoded average sentiment data for YouTube videos and news articles
youtube_data = [
    ('2024-05-10', {'positive': 17.58, 'neutral': 80.97, 'negative': 1.45}),
    ('2024-05-11', {'positive': 24.34, 'neutral': 63.95, 'negative': 11.72}),
    ('2024-05-12', {'positive': 23.82, 'neutral': 69.25, 'negative': 6.94}),
    ('2024-05-13', {'positive': 17.35, 'neutral': 78.24, 'negative': 4.41}),
    ('2024-05-14', {'positive': 20.64, 'neutral': 72.09, 'negative': 7.27}),
    ('2024-05-15', {'positive': 16.11, 'neutral': 71.57, 'negative': 12.32}),
    ('2024-05-16', {'positive': 25.79, 'neutral': 64.50, 'negative': 9.71}),
    ('2024-05-17', {'positive': 25.30, 'neutral': 65.67, 'negative': 9.04}),
    # ('2024-05-18', {'positive': 57.45, 'neutral': 35.61, 'negative': 6.95})
]

news_data = [
    ('2024-05-10', {'positive': 28.33, 'neutral': 53.33, 'negative': 18.33}),
    ('2024-05-11', {'positive': 33.67, 'neutral': 43.00, 'negative': 23.33}),
    ('2024-05-12', {'positive': 30.00, 'neutral': 56.67, 'negative': 13.33}),
    ('2024-05-13', {'positive': 36.67, 'neutral': 46.67, 'negative': 16.67}),
    ('2024-05-14', {'positive': 38.33, 'neutral': 45.00, 'negative': 16.67}),
    ('2024-05-15', {'positive': 43.33, 'neutral': 51.67, 'negative': 5.00}),
    ('2024-05-16', {'positive': 51.67, 'neutral': 38.33, 'negative': 10.00}),
    ('2024-05-17', {'positive': 58.33, 'neutral': 41.67, 'negative': 0.00})
]

# Hardcoded stock prices
stock_prices = pd.DataFrame({
    'Date': ['2024-05-17', '2024-05-16', '2024-05-15', '2024-05-14', '2024-05-13', '2024-05-10'],
    'Close/Last': [177.46, 174.84, 173.99, 177.55, 171.89, 168.47]
})


def plot_positive_sentiment(news_data, youtube_data, stock_prices):
    dates = [item[0] for item in news_data]

    news_positive = [item[1]['positive'] for item in news_data]
    youtube_positive = [item[1]['positive'] for item in youtube_data]

    stock_prices['Date'] = pd.to_datetime(stock_prices['Date'])
    stock_prices.set_index('Date', inplace=True)
    stock_prices = stock_prices.reindex(
        pd.to_datetime(dates)).interpolate().reset_index()

    stock_dates = stock_prices['index'].dt.strftime('%Y-%m-%d')
    stock_values = stock_prices['Close/Last']

    x = range(len(dates))

    plt.figure(figsize=(8, 6))
    plt.plot(x, news_positive, label='News Positive', marker='o')
    plt.plot(x, youtube_positive, label='YouTube Positive', marker='x')
    plt.plot(x, stock_values, label='Stock Prices', marker='s')
    plt.xticks(x, dates, rotation='vertical')
    plt.xlabel('Date')
    plt.ylabel('Percentage / Stock Price ($)')
    plt.title('Positive Sentiment & Stock Prices')
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_positive_sentiment(news_data, youtube_data, stock_prices)
