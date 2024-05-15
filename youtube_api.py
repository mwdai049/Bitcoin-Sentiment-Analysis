import requests


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

    def get_top_videos(self, channel_id, query, max_results=3):
        url = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'q': query,
            'maxResults': max_results,
            'type': 'video',
            'key': self.api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        video_ids = [item['id']['videoId'] for item in data['items']]
        return video_ids
