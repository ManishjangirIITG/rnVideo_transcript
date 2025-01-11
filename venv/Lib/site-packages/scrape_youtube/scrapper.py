from pytube import YouTube
from pytube import Playlist
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
import scrapetube
from bs4 import BeautifulSoup
import requests

pattern = re.compile('(?<=shortDescription":").*(?=","isCrawlable)')
pattern1= re.compile(r'(<title>|<\/?title>|\bYouTube\b)|[^\w\s]')

class YoutubeScrapper:
    def __init__(self):
        pass
    def single_video(self,url,out_path,audio_only=False,transcript=False,transcript_lang=None,description=False):
        try:
            v_id=url.split("v=")[1]
            soup = BeautifulSoup(requests.get(url).content)
            if description:
                description_text= pattern.findall(str(soup))[0].replace('\\n','\n')
            if transcript:
                transcript_list = YouTubeTranscriptApi.list_transcripts(v_id)
                if transcript_lang:
                    try:
                        transcript= transcript_list.find_transcript(transcript_lang)
                        transcript_text=transcript.fetch()

                    except:
                        transcript_english= transcript_list.find_transcript(['en'])
                        translated_transcript= transcript_english.translate(transcript_lang)
                        transcript_text=translated_transcript.fetch()

                else:
                    try:
                        transcript= transcript_list.find_transcript(['en'])
                        transcript_text=transcript.fetch()
                    except:
                        print("there is no tanscript available for default language english.please choose a language for which you want!")
            
                transcript_txt=" ".join([str({"start":el["start"],"duration":el["duration"],"text":el["text"]})+"\n" for el in transcript_text])
            yt = YouTube(url)
            print(yt.streams)
            video = yt.streams.filter(only_audio=audio_only).first()
            stream_destination=os.path.join(out_path,"stream")
            downlaoded_video=os.listdir(stream_destination)
            out_file = video.download(output_path=stream_destination)
            if audio_only:
                new_file = stream_destination+f"/{v_id}.wav"
            else:
                new_file = stream_destination+f"/{v_id}.mp4"

            basename=new_file.split('/')[-1]
            if basename in downlaoded_video:
                print("file is already downloaded")
                os.remove(out_file)
            else:
                os.rename(out_file,new_file)
                f = open(f"{out_path}/description/{v_id}.txt","w",encoding="utf-8")
                f.write(description_text)
                f.close()
                f = open(f"{out_path}/transcript/{v_id}.txt", "w", encoding="utf-8")
                f.write(transcript_txt)
                f.close()
                print("successfully dowloaded")
        except Exception as e:
            print(e)