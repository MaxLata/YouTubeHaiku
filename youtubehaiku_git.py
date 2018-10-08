# Reddit API wrapper
import praw

# Used for naming playlists with date
import datetime

# Used for YouTube API
import httplib2
import os
import sys
import google.oauth2.credentials
import google_auth_oauthlib.flow

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

from playlistadd import *
# Extracting links from r/youtubehaiku

# instantiate reddit object from PRAW
def main(c_id, c_sec, u_ag, un, pw):
    reddit = praw.Reddit(client_id=c_id,
                         client_secret=c_sec,
                         user_agent=u_ag,
                         username=un,
                         password=pw)

    # get specific ythaiku subreddit object and collect its top 25 links
    ythaiku = reddit.subreddit('youtubehaiku')
    topLinks = ythaiku.hot(limit=25)

    # initialize empty list of YouTube video IDs
    idList = []
    for post in topLinks:
        print(post.url)

    # loop over top links
    for post in topLinks:
        url = post.url

        # if the url is shortened for sharing
        # ex: https://youtu.be/UI0n7ElZkHY
        if url.startswith("https://youtu."):
            splitOnBe = url.split("be/")
            splitOnQMark = splitOnBe[1].split("?")
            idList.append(splitOnQMark[0])
        # if not shortened
        # ex: https://www.youtube.com/watch?v=Jcghl0lbDSk
        else:
            splitOnEquals = url.split("?v=")
            splitOnAmp = splitOnEquals[1].split("&feature")
            idList.append(splitOnAmp[0])

    # Get the date for playlist name
    date = datetime.datetime.today().strftime('%m-%d-%y')

    # Making YouTube playlist

    CLIENT_SECRETS_FILE = "client_secret.json"

    # This OAuth 2.0 access scope allows for full read/write access to the
    # authenticated user's account.
    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
      scope=YOUTUBE_READ_WRITE_SCOPE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
      flags = argparser.parse_args()
      credentials = run_flow(flow, storage, flags)

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      http=credentials.authorize(httplib2.Http()))

    # This code creates a new, private playlist in the authorized user's channel.
    playlists_insert_response = youtube.playlists().insert(
      part="snippet,status",
      body=dict(
        snippet=dict(
          title=date,
          description="Playlist of the top 25 r/youtubehaiku videos from " + date
        ),
        status=dict(
          privacyStatus="public"
        )
      )
    ).execute()

    playlistID = playlists_insert_response["id"]
    print(playlistID)

    # Adding videos to playlist
    for videoID in idList:
        playlist_items_insert(youtube,
          {'snippet.playlistId': playlistID,
           'snippet.resourceId.kind': 'youtube#video',
           'snippet.resourceId.videoId': videoID,
           'snippet.position': ''},
          part='snippet')
