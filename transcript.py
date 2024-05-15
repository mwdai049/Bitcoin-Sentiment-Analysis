from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptProcessor:
    def get_transcript(self, video_id):
        lines = YouTubeTranscriptApi.get_transcript(video_id)
        return [line['text'] for line in lines]

    def preprocess_transcript(self, transcript):
        # Split transcript into segments of 5 lines each
        new_lst = []
        for i in range(0, len(transcript), 5):
            lines = transcript[i:i+5]
            into_one = ' '.join(lines)
            new_lst.append(into_one)
        return new_lst
