

import os
import requests.auth
#from apiclient.discovery import build
#from google-api-python-client.discovery import build
from googleapiclient.discovery import build

class youtube_api_wrapper:
    API_KEY = ""
    youtube = None
    req_cnt = 0

    def __init__(self):        
        API_KEY = os.environ['YOUTUBE_API_KEY']
        self.youtube = build('youtube', 'v3', developerKey=API_KEY)
        self.req_cnt = 0

    def do_req(self, api_type, **kwargs):

        self. req_cnt += 1
        if api_type == "search":
            req = self.youtube.search().list(**kwargs)

        elif api_type == "videos":
            req = self.youtube.videos().list(**kwargs)

        elif api_type == "commentThreads":
            req = self.youtube.commentThreads().list(**kwargs)

        elif api_type == "comments":
            req = self.youtube.comments().list(**kwargs)
        
        return req.execute()

