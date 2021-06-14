from db_builder.models import *

def all_infixs():
    for i in Infixation.objects.all():
        print(i.infixation)

def poo():
    print("poo")

def get_wet():
    print("Here are the infixations from 2wet")
    for i in Infixation.objects.filter(vid_title="2 Wet Crew: 2 Sog Squad pt. 3"):
        print(i.vid_title)

    print("Here are the checked_vids from 2wet")
    for x in Checked_Vids.objects.filter(vid_title="2 Wet Crew: 2 Sog Squad pt. 3"):
        print(x.vid_title)

def clear_2wet():
    for cv in Checked_Vids.objects.all().filter(vid_title="2 Wet Crew: 2 Sog Squad pt. 3"):
        cv.delete()
    for i in Infixation.objects.filter(vid_title="2 Wet Crew: 2 Sog Squad pt. 3"):
        i.delete()
#from db_builder.help import *

#2 Wet Crew: 2 Sog Squad pt. 3


