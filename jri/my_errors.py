class ErrorCheckingThreadReplies(Exception):
    def __init__(self, comment_thread_id, vid_id):
        self.comment_thread_id = comment_thread_id
        self.vid_id = vid_id
        str = f'Error checking comment-thread replies, comment-thread id={self.comment_thread_id}'
        str = str + f' vid_id={vid_id}'
        super().init(str)

class ErrorGettingNextCommentThreads(Exception):
    def __init__(self, next_page_token, vid_id):
        self.vid_id = vid_id
        self.next_page_token = next_page_token
        str = f'Error getting next comment-thread, nextPageToken={next_page_token}'
        str = str + f' vid_id={vid_id}'
        super().init(str)