import sys, os, math, re, datetime
import requests.auth
from enum import Enum
#from apiclient.discovery import build
from youtube_api_wrapper import youtube_api_wrapper

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jri.settings")
import django
django.setup()
from db_builder.models import Infixation, Checked_Vids, Checked_CommentThreads
from django.utils import timezone

# youtubes api's per request response item limits
SEARCH_MAX_RESULTS = 50
COMMENT_THREAD_MAX_RESULTS = 100
COMMENT_MAX_RESULTS = 100

API_KEY = os.environ['YOUTUBE_API_KEY']

regex = re.compile(r'[jJ][oO][eE] *"[^"]*" *[rR][oO][gG][aA][nN]')

def write_to_log_and_print(logfile, msg):
    logfile.write(msg)
    print(msg)

def menu_exit():
    print("exiting")
    sys.exit()

def menu_print_all_infixations():
    print('showing all infixations...')
    all_infixations = Infixation.objects.all()
    num_of_infixations = len(all_infixations)
    print(f'Total number of infixations recorded: {str(num_of_infixations)}')
    for i in all_infixations:
        print( f'infixation: {i.infixation}, source video: {i.vid_title}' )

class State(Enum):
    MAIN_MENU = 0

class MenuOpts(Enum):
    QUIT = 0
    SHOW_ALL_INFIXATIONS = 1
    WRITE_INFIXATIONS_TO_FILE = 2
    SEARCH_FOR_NEW_INFIXATIONS = 3

def process_comment(comment, v_id, v_title, ct_id, c_id, c_date):
    res = regex.search(comment)
    if res:
        print(f'Got infixation: {res[0]}')
        Infixation(infixation=res[0], vid_id=v_id, comment_thread_id=ct_id,\
             comment_id=c_id, vid_title=v_title, \
                 date_added=datetime.datetime(int(c_date[0:4]),\
                                             int(c_date[5:7]),\
                                            int(c_date[8:10])
                                            )).save()

def check_one_comment_thread():
    pass

def check_replies_to_thread(thread_item):
    if 'replies' not in thread_item:
        pass
    #If all replies included in the current request response
    elif thread_item['snippet']['totalReplyCount'] == len(thread_item['replies']['comments']):
        for comment in thread_item['replies']['comments']:
            write_to_log_and_print(logfile, 'reply comment: ' + comment['snippet']['textOriginal']+'\n')
            process_comment(comment['snippet']['textOriginal'],\
                videoId, videoTitle, thread_item['id'],thread_item["snippet"]["topLevelComment"]['id'],\
                    comment['snippet']['publishedAt'])
    #If further requests are neccesary to get all the comments.
    else:
        write_to_log_and_print(logfile, f'Getting all comments from "comment" resource.\n')
        res_comments = youtube.do_req(api_type="comments", part="snippet", parentId=thread_item["id"], maxResults=COMMENT_MAX_RESULTS)
        reply_pages_remaining = True
        while reply_pages_remaining:
            for comment in res_comments['items']:
                write_to_log_and_print(logfile, f'Comment: {comment["snippet"]["textOriginal"]}\n')
                process_comment(comment['snippet']['textOriginal'],\
                    videoId, videoTitle, thread_item['id'],thread_item["snippet"]["topLevelComment"]['id'],\
                        comment['snippet']['publishedAt'])
  
            reply_pages_remaining = True if 'nextPageToken' in res_comments else False

            if reply_pages_remaining:
                res_comments = youtube.do_req(api_type="comments", part="snippet", parentId=thread_item["id"], maxResults=COMMENT_MAX_RESULTS, pageToken=res_comments['nextPageToken'])


def show_menu_options():
    print('Choose one of...')
    for i in MenuOpts:
        print (str(i.value) + ' ' + i.name)

if __name__ == "__main__":

    api_req_cnt = 0
    
    print('Starting...')


    while True:

        show_menu_options()
        choice = int(input())

        if choice == MenuOpts.QUIT.value:
            menu_exit()

        elif choice == MenuOpts.SHOW_ALL_INFIXATIONS.value:
            menu_print_all_infixations()
        
        elif choice == MenuOpts.WRITE_INFIXATIONS_TO_FILE.value:
            print("to file is unimplemented")
            pass

        elif choice == MenuOpts.SEARCH_FOR_NEW_INFIXATIONS.value:
            inp = input('enter search string/ or 0 to go back: ')

            with open('get.log', 'a+', encoding='UTF-8') as logfile:

                youtube = youtube_api_wrapper()

                logfile.write(f'STARTING AT {timezone.now()}\n')
                write_to_log_and_print(logfile, f'Searching for: {inp}\n')
                res_search = youtube.do_req(api_type="search", part="snippet", q=inp, type="video", maxResults=SEARCH_MAX_RESULTS)

                write_to_log_and_print(logfile, f'Total of {res_search["pageInfo"]["totalResults"]} results\n')
                num_of_vids_to_check = int(input('How many of those results do want to check?'))
                search_pages_to_check = math.ceil(num_of_vids_to_check/res_search['pageInfo']['resultsPerPage'])
                
                checkRes = input(f'That will require checking {search_pages_to_check} page(s) - and approximately - are you sure?(Y/n) ')
                if checkRes == 'Y' or checkRes == 'y':
                    
                    while num_of_vids_to_check > 0 and search_pages_to_check > 0:

                        for vid in res_search['items']:
                            #Even if we haven't done every vid in this page of video results, we might have looked through
                            #the number of videos requested to check.
                            if num_of_vids_to_check == 0:
                                break

                            videoId = vid['id']['videoId']
                            videoTitle = vid['snippet']['title']
                            if len(Checked_Vids.objects.filter(vid_id=videoId)) > 0:
                                write_to_log_and_print(logfile, f'Video in search already checked : {videoTitle} - {videoId}\n')
                            else:
                                res_vid = youtube.do_req(api_type="videos", part="statistics,snippet", id=videoId)
                                commentCnt = res_vid["items"][0]["statistics"]["commentCount"]
                                write_to_log_and_print(logfile, f'Comment count for {videoId} is: {commentCnt}\n')

                                res_thread = youtube.do_req(api_type="commentThreads", part="snippet,replies,id", maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId)

                                has_more_top_comments = True

                                while has_more_top_comments:

                                    for thread in res_thread['items']:
                                        try:
                                            write_to_log_and_print(logfile, f'Top level comment: {thread["snippet"]["topLevelComment"]["snippet"]["textOriginal"]}\n')
                                        except Exception as e:
                                            print(e)
                                            print("")

                                        process_comment(thread["snippet"]["topLevelComment"]["snippet"]["textOriginal"],\
                                            videoId, videoTitle, thread['id'],thread["snippet"]["topLevelComment"]['id'],\
                                                thread["snippet"]["topLevelComment"]['snippet']['publishedAt'])

                                        write_to_log_and_print(logfile, f'Has {thread["snippet"]["totalReplyCount"]} reply(ies)\n')

                                        if 'replies' not in thread:
                                            write_to_log_and_print(logfile, 'No replies to that comment.\n')
                                            pass
                                        elif thread['snippet']['totalReplyCount'] == len(thread['replies']['comments']):
                                            write_to_log_and_print(logfile, f'All replies fitted in the top level comment request.\n')
                                            for comment in thread['replies']['comments']:
                                                write_to_log_and_print(logfile, 'reply comment: ' + comment['snippet']['textOriginal']+'\n')
                                                process_comment(comment['snippet']['textOriginal'],\
                                                        videoId, videoTitle, thread['id'],thread["snippet"]["topLevelComment"]['id'],\
                                                            comment['snippet']['publishedAt'])
                                        #When we need to get replies page by page from a top-level comment
                                        else:
                                            write_to_log_and_print(logfile, f'Getting all comments from "comment" resource.\n')
                                            res_comments = youtube.do_req(api_type="comments", part="snippet", parentId=thread["id"], maxResults=COMMENT_MAX_RESULTS)
                                            reply_pages_remaining = True
                                            while reply_pages_remaining:
                                                for comment in res_comments['items']:
                                                    write_to_log_and_print(logfile, f'Comment: {comment["snippet"]["textOriginal"]}\n')
                                                    process_comment(comment['snippet']['textOriginal'],\
                                                        videoId, videoTitle, thread['id'],thread["snippet"]["topLevelComment"]['id'],\
                                                            comment['snippet']['publishedAt'])
                                                
                                                reply_pages_remaining = True if 'nextPageToken' in res_comments else False

                                                if reply_pages_remaining:
                                                    res_comments = youtube.do_req(api_type="comments", part="snippet", parentId=thread["id"], maxResults=COMMENT_MAX_RESULTS, pageToken=res_comments['nextPageToken'])
                                    
                                    has_more_top_comments = True if 'nextPageToken' in res_thread else False

                                    if has_more_top_comments:
                                        res_thread = youtube.do_req(api_type="commentThreads", part="snippet,replies,id", maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId, pageToken=res_thread['nextPageToken'])

                            checked_vid = Checked_Vids(vid_id=videoId, vid_title=videoTitle)
                            checked_vid.save()
                            num_of_vids_to_check -= 1
                        
                        search_pages_to_check -= 1
                        if search_pages_to_check > 0:
                            res_search = youtube.do_req(api_type="search", part="snippet", q=inp, type="video", maxResults=SEARCH_MAX_RESULTS, pageToken=res_search['nextPageToken'])

                logfile.write(f'ENDING - used a total of {api_req_cnt} api requests\n\n')
                logfile.close()


