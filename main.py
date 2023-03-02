from requests import post, get
import json
from dotenv import load_dotenv
import os
import base64
import pandas as pd
from googleapiclient.discovery import build
import pytube


def get_token():
    auth_string=client_id+":"+client_secret
    auth_base64=base64.urlsafe_b64encode(auth_string.encode()).decode()

    url="https://accounts.spotify.com/api/token"
    headers = {
        "Authorization" : "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data={"grant_type": "client_credentials"}
    result=post(url=url,headers=headers,data=data)
    json_result=json.loads(result.content)
    token=json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer "+token}

def search_playlists(token,playlist_title,limit):
    url="https://api.spotify.com/v1/search"
    headers=get_auth_header(token=token)
    query=f'q={playlist_title}&type=playlist&limit={limit}'
    query_url=url+'?'+query
    result=get(query_url,headers=headers)
    json_result=json.loads(result.content)['playlists']['items']
    return json_result

def get_playlist_info(token,playlist_id):
    url=f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers=get_auth_header(token=token)
    result=get(url,headers=headers)
    json_result=json.loads(result.content)
    return(json_result)

def export_songs_csv(file_name_output,playlist_title):
    durations=[]
    names=[]
    artists=[]
    songs={"duration":durations, "names":names, 'artists': artists}
    token=get_token()
    playlists=search_playlists(token=token, playlist_title=f"{playlist_title}",limit=2)
    total_duration=0
    for i in playlists:
        playlist_id=(i['id'])
        playlist_info=get_playlist_info(token=token,playlist_id=playlist_id)
        items=playlist_info['items']
        for i in items:
            track=(i['track'])
            name=track['name']
            duration=track['duration_ms']
            for j in track['artists']:
                artist=(j['name'])
            total_duration+=int(duration)
            durations.append(duration)
            names.append(name)
            artists.append(artist)

    songs_df=pd.DataFrame.from_dict(songs)
    songs_df.to_csv(f'{file_name_output}.csv')
    print('Database created')
    return(f'{file_name_output}.csv')

def clean_data(file_name_input,file_name_output):
    songs_df=pd.read_csv(f'{file_name_input}')
    songs_df.drop(['Unnamed: 0'],axis=1,inplace=True)
    songs_df.drop_duplicates(['names'],keep='first',inplace=True)
    songs_df.to_csv(f'{file_name_output}.csv')
    print('duplicates have been deleted')
    return f'{file_name_output}.csv'

def search_video_by_keywords(keywords):
    request=youtube.search().list(
        part='snippet',
        maxResults=1,
        q=f'{keywords}'
    )
    return request.execute()

def get_video_id(search_snippet):
    items=search_snippet['items']
    items_dict=items[0]
    id_dict=items_dict['id']
    try:
        print('video found')
        return id_dict['videoId']
    except:
        print('video not found')
        return 'None'

def get_id_list(dataframe_name):
    video_ids=[]
    dataframe=pd.read_csv(f'{dataframe_name}')
    #for i in range(len(dataframe['names'])):
    for i in range(50):
        name_list=[]
        separator=' '
        name_list.append(dataframe['names'][i])
        name_list.append(dataframe['artists'][i])
        name=separator.join(name_list)
        snippet=search_video_by_keywords(name)
        video_ids.append(get_video_id(snippet))
    return video_ids

def download_audio(id_list):
    partial_url='https://www.youtube.com/watch?v='
    for i in id_list:
        try:
            vid=yt(f'{partial_url}{i}')
            vid.streams.filter(only_audio=True).first().download('./audio_downloads')
            print(f'Element {id_list.index(i)} downloaded')
        except:
            print(f'element {id_list.index(i)} not found or is not a video')
    print('Finished downloading elements')

if __name__=="__main__":

    #loading APIs
    load_dotenv()
    client_id=os.getenv("SPOTIFY_CLIENT_ID") #your spotify client API
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET") #your spotify secret API
    youtube_client_api=os.getenv("YOUTUBE_CLIENT_ID") #your youtube client API

    #youtube and pytube config
    youtube=build('youtube','v3',developerKey=youtube_client_api) 
    yt=pytube.YouTube

    # what do you wanna search?
    playlist_title="your playlist here"
    
    # execution
    dataframe=export_songs_csv('song_dataframe',playlist_title)
    clean_dataframe=clean_data(dataframe,'clean_dataframe')
    video_ids=get_id_list(clean_dataframe)
    download_audio(video_ids)
    print('done')