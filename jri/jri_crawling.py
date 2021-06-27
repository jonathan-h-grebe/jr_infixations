import sys, os, math, re, datetime
import requests.auth
from enum import Enum
from youtube_api_wrapper import youtube_api_wrapper
from my_errors import ErrorCheckingThreadReplies, ErrorGettingNextCommentThreads

import django
django.setup()
from db_builder.models import Infixation, Checked_Vids, Part_Checked_Vids
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
        if len(Infixation.objects.filter(vid_title=v_title, comment_id=c_id, infixation=res[0])) == 0:
            print(f'Got new infixation: {res[0]}\n')
            Infixation(infixation=res[0], vid_id=v_id, comment_thread_id=ct_id,\
                   comment_id=c_id, vid_title=v_title, \
                   date_added= make_aware (datetime.datetime(int(c_date[0:4]),\
                                            int(c_date[5:7]),\
                                            int(c_date[8:10]))
                                            ),
                   likes=like_count).save()

def print_first_five_vid_titles(res_search):
    print(f'Total of {res_search["pageInfo"]["totalResults"]} results\n')
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


def make_initial_ct_req(videoId, youtube):
    #Make first request for comment threads for given video.

    #If this video was partially checked previously, but checking was aborted
    #due to some exception and the last pagen token was saved, start looking
    #from that page token.
    if vid_partially_checked(videoId):
        next_page_token = Part_Checked_Vids.objects.get(vid_id=videoId).next_page_token
        return youtube.do_req(api_type="commentThreads", part="snippet,replies,id",
                              maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId,
                              pageToken=next_page_token)
    else:
        return youtube.do_req(api_type="commentThreads", part="snippet,replies,id",
                              maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId)


def check_one_vid(videoId, videoTitle, num_of_vids_to_check, vid, youtube, logfile):
    res_vid = youtube.do_req(api_type="videos", part="statistics,snippet", id=videoId)
    commentCnt = get_comment_count_from_vid(res_vid)

    if video_has_already_been_checked(videoId):
        return
    proceed = input(f'Video 「{videoTitle}」has {commentCnt} comment thead(s). Proceed?(Y/n) ')
    if (proceed != 'Y' and proceed != 'y'):
        print("skipping this video")
        return

    write_to_log_and_print(logfile, f'Comment count for {videoId} is: {commentCnt}\n')
    reqs_made_at_start = youtube.req_cnt

    ct_next_page_token = ''

    #if its a comment-thread that failed before, add the next-page token to this request,
    #in order to fast forward to that comment thread.
    res_thread = make_initial_ct_req(videoId, youtube)

    print(f'Checking comment {youtube.req_cnt- reqs_made_at_start} of {commentCnt}', end='\r')
    has_more_top_comments = True
    try:
        while has_more_top_comments:

            for thread in res_thread['items']:

                write_to_log_and_print(logfile, f'Top level comment: {top_text_from_thread(thread)}\n')

                process_comment(top_text_from_thread(thread), videoId, videoTitle, thread['id'],\
                                topcommentid_from_thread(thread), top_comment_date_from_thread(thread),\
                                COMMENT_COUNT_UNAVAILABLE)

                write_to_log_and_print(logfile, f'Has {thread["snippet"]["totalReplyCount"]} reply(ies)\n')

                try:
                    check_replies_to_thread(thread, videoId, videoTitle, logfile, youtube)
                except Exception as e:
                    raise(ErrorCheckingThreadReplies(thread["id"]), videoId)

            has_more_top_comments = top_comments_remaining(res_thread)
            if has_more_top_comments:
                try:
                    ct_next_page_token = res_thread['nextPageToken']
                    res_thread = youtube.do_req(api_type="commentThreads", part="snippet,replies,id",
                                                maxResults=COMMENT_THREAD_MAX_RESULTS, videoId=videoId, 
                                                pageToken=ct_next_page_token)
                    print(f'Checking comment {youtube.req_cnt- reqs_made_at_start} of {commentCnt}', end='\r')
                except Exception as e:
                    raise(ErrorGettingNextCommentThreads(ct_next_page_token), videoId)

    except ErrorCheckingThreadReplies as e:
        #API request returned error, so give up on this video but save where we checked up until
        #so that next time the same video is checked, it isn't necessary to go back to the start.
        Part_Checked_Vids(vid_id=videoId, next_page_token=ct_next_page_token, vid_title=videoTitle).save()
        print(f'Aborting checking of video "{videoTitle}"" due to google api exception')
    except ErrorGettingNextCommentThreads as e:
        #TODO: implement handling for this properly. Temporary measure: just do the same as ErrorCheckingThreadReplies 
        Part_Checked_Vids(vid_id=videoId, next_page_token=ct_next_page_token, vid_title=videoTitle).save()


def vid_partially_checked(videoId):
    if len(Part_Checked_Vids.objects.filter(vid_id=videoId)) > 0:
        if Part_Checked_Vids.objects.get(vid_id).next_page_token != '':
            return True
    return False

def search_for_new_infixations():
    inp = input('enter search string/ or 0 to go back: ')

    with open('get.log', 'a+', encoding='UTF-8') as logfile:

        youtube = youtube_api_wrapper()

        logfile.write(f'STARTING AT {timezone.now()}\n')
        res_search = youtube.do_req(api_type="search", part="snippet", q=inp, type="video", maxResults=SEARCH_MAX_RESULTS)

        write_to_log_and_print(logfile, f'\nTotal of {res_search["pageInfo"]["totalResults"]} results\n')
        print_first_five_vid_titles(res_search)

        num_of_vids_to_check = int(input('How many of those results do want to check?'))
        search_pages_to_check = get_pages_to_check(res_search, num_of_vids_to_check)
        
        
        checkRes = input(f'That requires {search_pages_to_check} page(s) of search results. OK?(Y/n) ')
        if checkRes == 'Y' or checkRes == 'y':
            
            while num_of_vids_to_check > 0 and search_pages_to_check > 0:

                for x, vid in enumerate(res_search['items']):
                    #Even if we haven't done every vid in this page of video results, we might have looked through
                    #the number of videos requested to check.
                    if num_of_vids_to_check == 0:
                        break
                    else:
                        print(f'Checking vid {x+1} of {num_of_vids_to_check}: \n')
                        videoId = vid['id']['videoId']
                        videoTitle = vid['snippet']['title']
                        check_one_vid(videoId, videoTitle, num_of_vids_to_check, vid, youtube, logfile)

                    save_new_checked_video(videoId, videoTitle)
                    num_of_vids_to_check -= 1
                
                search_pages_to_check -= 1
                if search_pages_to_check > 0:
                    res_search = youtube.do_req(api_type="search", part="snippet", q=inp, type="video",
                                                maxResults=SEARCH_MAX_RESULTS, pageToken=res_search['nextPageToken'])

        logfile.write(f'Finished going through videos based on search string.\nMade a total of {youtube.req_cnt} reqs to Google API.\n\n')
        print(f'Finished going through videos based on search string.\nMade a total of {youtube.req_cnt} reqs to Google API.')
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

