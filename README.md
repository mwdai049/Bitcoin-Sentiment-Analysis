# Stock Market Sentiment Analysis

This project aims to analyze the sentiment of news articles and YouTube videos related to a specific stock (Bitcoin in this case) and correlate it with the stock's price over a period of time. The project uses sentiment analysis models and various APIs to gather data, process it, and visualize the results.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Project Structure](#project-structure)

## Overview

The project fetches and analyzes sentiment from news articles and YouTube videos related to Bitcoin. It then visualizes the sentiment trends alongside the Bitcoin closing prices.

## Features

- Fetch news articles and YouTube videos related to Bitcoin.
- Perform sentiment analysis on the fetched data.
- Visualize sentiment trends and correlate them with Bitcoin's closing prices.
- Summarize daily sentiment data for both news and YouTube content.

## Requirements

- Python 3.8 or higher
- `googleapiclient`
- `youtube-transcript-api`
- `transformers`
- `beautifulsoup4`
- `pandas`
- `matplotlib`
- `requests`
- `python-dotenv`

## Setup

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/Stock-Market-Sentiment-Analysis.git
   cd Stock-Market-Sentiment-Analysis

   ```

2. Install the required Python packages:
   `pip install -r requirements.txt`

3. Set up your environment variables:
   Create a .env file in the root directory.
   Create your API keys for the [News API] (https://newsapi.org/) and [YouTube Data API] (https://console.developers.google.com/).
   Add your API keys to the .env file:
   `YOUTUBE_API_KEY=replace_with_your_youtube_api_key`
   `NEWS_API_KEY=replace_with_your_news_api_key`

4. Place your Bitcoin CSV data file in the /data directory and ensure it is named BTC-USD.csv.

## Usage

To run the project, execute the main script:

```sh
python main.py
```

The script will:

1. Fetch news articles and YouTube videos from the past 10 days related to Bitcoin.
2. Perform sentiment analysis on the fetched content.
3. Visualize the sentiment trends and correlate them with Bitcoin's closing prices (from the past 10 days).
4. Output a summary of the sentiment analysis.

## Data Sources

News Articles: Fetched using the [News API] (https://newsapi.org/).
YouTube Videos: Fetched using the [YouTube Data API] (https://console.developers.google.com/).
Sentiment Analysis Model: Using the [ProsusAI FinBERT model] (https://huggingface.co/ProsusAI/finbert).
Stock Prices: Loaded from a CSV file (BTC-USD.csv).

## Project Structure

- `main.py`: The main script that runs the project.
- `news_sentiment.py`: Contains the NewsSentimentAnalyzer class to analyze news article sentiments.
- `youtube_sentiment.py`: Contains functions for extracting and analyzing YouTube video transcripts.
- `data/`: Directory to store the CSV file containing Bitcoin prices.
- `transcripts/`: Directory to store fetched YouTube video transcripts.
- `.env`: Environment variables file (not included in the repository).
- `requirements.txt`: List of Python packages required for the project.
