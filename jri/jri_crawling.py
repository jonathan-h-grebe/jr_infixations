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
from django.utils.timezone import make_aware

# youtubes api's per request response item limits
SEARCH_MAX_RESULTS = 50
COMMENT_THREAD_MAX_RESULTS = 100
COMMENT_MAX_RESULTS = 100

Checked_Vids.objects.all()

COMMENT_COUNT_UNAVAILABLE = -1


API_KEY = os.environ['YOUTUBE_API_KEY']

regex = re.compile(r'[jJ][oO][eE] *"[^"]*" *[rR][oO][gG][aA][nN]')

def get_pages_to_check(res_search, num_of_vids_to_check):
    if res_search['pageInfo']['resultsPerPage'] == 0:
        return 0
    return math.ceil(num_of_vids_to_check/res_search['pageInfo']['resultsPerPage'])

def write_to_log_and_print(logfile, msg):
    logfile.write(msg)
    #print(msg)

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

def text_from_comment(comment):
    return comment['snippet']['textOriginal']
def date_from_comment_stuct(comment):
    return comment['snippet']['publishedAt']
def topcommentid_from_thread(thread_object):
    return thread_object["snippet"]["topLevelComment"]['id']
def topcommentlines_from_thread(thread_object):
    return thread_object["snippet"]["topLevelComment"]["likeCount"]
def top_text_from_thread(thread_object):
    return thread_object["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
def top_comment_date_from_thread(thread_object):
    return thread_object["snippet"]["topLevelComment"]['snippet']['publishedAt']
def likes_from_comment(comment):
    return comment['snippet']['likeCount']
def get_comment_count_from_vid(res_vid):
    return res_vid["items"][0]["statistics"]["commentCount"]

def top_comments_remaining(res_thread):
    return True if 'nextPageToken' in res_thread else False

def reply_pages_remaining(res_comments):
    if 'nextPageToken' in res_comments:
        return True
    return False

def top_comments_remaining(res_thread):
    return True if 'nextPageToken' in res_thread else False

def process_comment(comment, v_id, v_title, ct_id, c_id, c_date, like_count):
    res = regex.search(comment)
    if res:
        print(f'Got infixation: {res[0]}')
        Infixation(infixation=res[0], vid_id=v_id, comment_thread_id=ct_id,\
             comment_id=c_id, vid_title=v_title, \
                 date_added= make_aware (datetime.datetime(int(c_date[0:4]),\
                                             int(c_date[5:7]),\
                                            int(c_date[8:10]))
                                            ), likes=like_count).save()

def print_first_five_vid_titles(res_search):
    for x in range(0,min(4, len(res_search['items']))):
        str = res_search['items'][x]['snippet']['title']
        if video_has_already_been_checked(res_search['items'][x]['id']['videoId']):
            str = str + " *** ALREADY CHECKED - will be skipped"
        print(str)
    print("...\n")

def save_new_checked_video(videoId, videoTitle):
    Checked_Vids(vid_id=videoId, vid_title=videoTitle).save()

def check_replies_to_thread(thread_item, videoId, videoTitle, logfile, youtube):
    if 'replies' not in thread_item: pass
        
    #If all replies included in the current request response
    elif thread_item['snippet']['totalReplyCount'] == len(thread_item['replies']['comments']):
        for comment in thread_item['replies']['comments']:
            process_comment(text_from_comment(comment), videoId, videoTitle, thread_item['id'],\
                            comment['id'], date_from_comment_stuct(comment), 
                            likes_from_comment(comment))
                     
    #If further requests are neccesary to get all the comments.
    else:
        write_to_log_and_print(logfile, f'Getting all comments from "comment" resource.\n')
        res_comments = youtube.do_req(api_type="comments", part="snippet", parentId=thread_item["id"], maxResults=COMMENT_MAX_RESULTS)

        while True:
            for comment in res_comments['items']:
                write_to_log_and_print(logfile, f'Comment: {text_from_comment(comment)}\n')

                process_comment(text_from_comment(comment), videoId, videoTitle,\
                                thread_item['id'], comment['id'], date_from_comment_stuct(comment), 
                                likes_from_comment(comment))     

            if reply_pages_remaining(res_comments):
                res_comments = youtube.do_req(api_type="comments", part="snippet",
                                              parentId=thread_item["id"], 
                                              maxResults=COMMENT_MAX_RESULTS,
                                              pageToken=res_comments['nextPageToken'])
            else: break

def video_has_already_been_checked(videoId):
    if len(Checked_Vids.objects.filter(vid_id=videoId)) > 0:
        return True
    return False

def show_menu_options():
    print('Choose one of...')
    for i in MenuOpts:
        print (str(i.value) + ' ' + i.name)

def search_for_new_infixations():
    inp = input('enter search string/ or 0 to go back: ')

    with open('get.log', 'a+', encoding='UTF-8') as logfile:

        youtube = youtube_api_wrapper()

        logfile.write(f'STARTING AT {timezone.now()}\n')
        write_to_log_and_print(logfile, f'Searching for: {inp}\n')
        res_search = youtube.do_req(api_type="search", part="snippet", q=inp, type="video", maxResults=SEARCH_MAX_RESULTS)

        write_to_log_and_print(logfile, f'\nTotal of {res_search["pageInfo"]["totalResults"]} results\n')
        print(f'Total of {res_search["pageInfo"]["totalResults"]} results\n')
        print_first_five_vid_titles(res_search)

        num_of_vids_to_check = int(input('How many of those results do want to check?'))
        search_pages_to_check = get_pages_to_check(res_search, num_of_vids_to_check)
        
        
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
                    if video_has_already_been_checked(videoId):
                        write_to_log_and_print(logfile, f'Video in search already checked : {videoTitle} - {videoId}\n')
                    else:
                        res_vid = youtube.do_req(api_type="videos", part="statistics,snippet", id=videoId)
                        commentCnt = get_comment_count_from_vid(res_vid)
                        write_to_log_and_print(logfile, f'Comment count for {videoId} is: {commentCnt}\n')

                        res_thread = youtube.do_req(api_type="commentThreads", part="snippet,replies,id",
                                                    maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId)
                        has_more_top_comments = True
                        while has_more_top_comments:

                            for thread in res_thread['items']:
                                try:
                                    write_to_log_and_print(logfile, f'Top level comment: {top_text_from_thread(thread)}\n')
                                except Exception as e:
                                    print(f'{e}\n')

                                process_comment(top_text_from_thread(thread), videoId, videoTitle, thread['id'],\
                                                topcommentid_from_thread(thread), top_comment_date_from_thread(thread),\
                                                COMMENT_COUNT_UNAVAILABLE)

                                write_to_log_and_print(logfile, f'Has {thread["snippet"]["totalReplyCount"]} reply(ies)\n')

                                check_replies_to_thread(thread, videoId, videoTitle, logfile, youtube)
                            
                            has_more_top_comments = top_comments_remaining(res_thread)
                            if has_more_top_comments:
                                res_thread = youtube.do_req(api_type="commentThreads", part="snippet,replies,id", maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId, pageToken=res_thread['nextPageToken'])

                    save_new_checked_video(videoId, videoTitle)
                    num_of_vids_to_check -= 1
                
                search_pages_to_check -= 1
                if search_pages_to_check > 0:
                    res_search = youtube.do_req(api_type="search", part="snippet", q=inp, type="video", maxResults=SEARCH_MAX_RESULTS, pageToken=res_search['nextPageToken'])

        logfile.write(f'ENDING - used a total of {api_req_cnt} api requests\n\n')
        logfile.close()


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
            search_for_new_infixations()

