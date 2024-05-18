import requests
from datetime import datetime, timedelta


class YouTubeAPI:
    def __init__(self, api_key, channel_name):
        self.api_key = api_key
        self.channel_name = channel_name
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def get_channel_id(self):
        url = f"{self.base_url}/channels"
        params = {
            'part': 'id',
            'forHandle': self.channel_name,
            'key': self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['id']
        else:
            raise ValueError(f"No channel found: {self.channel_name}")

    def get_top_videos(self, channel_id, query, start_date, end_date, max_results=3):
        url = f"{self.base_url}/search"

        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'q': query,
            'maxResults': max_results,
            'type': 'video',
            'publishedAfter': start_date,
            'publishedBefore': end_date,
            'key': self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        video_ids = [item['id']['videoId'] for item in data['items']]
        return video_ids

    def get_business_days(self, num_days):
        business_days = []
        current_day = datetime.utcnow()
        while len(business_days) < num_days:
            if current_day.weekday() < 5:  # Monday to Friday are considered business days
                business_days.append(current_day)
            current_day -= timedelta(days=1)
        return business_days

    def get_videos_for_business_days(self, channel_id, query, num_days=10, videos_per_day=3):
        business_days = self.get_business_days(num_days)
        all_videos = []

        for day in business_days:
            start_date = day.replace(
                hour=0, minute=0, second=0, microsecond=0).isoformat("T") + "Z"
            end_date = (day + timedelta(days=1)).replace(hour=0,
                                                         minute=0, second=0, microsecond=0).isoformat("T") + "Z"
            videos = self.get_top_videos(
                channel_id, query, start_date, end_date, max_results=videos_per_day)
            all_videos.append({
                'date': day.date(),
                'videos': videos
            })

        return all_videos
