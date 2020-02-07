import json
import requests
import time
import threading
from download import *


class twitter_api:
	params={
		"include_profile_interstitial_type":"1",
		"include_blocking":"1",
		"include_blocked_by":"1",
		"include_followed_by":"1",
		"include_want_retweets":"1",
		"include_mute_edge":"1",
		"include_can_dm":"1",
		"include_can_media_tag":"1",
		"skip_status":"1",
		"cards_platform":"Web-12",
		"include_cards":"1",
		"include_composer_source":"true",
		"include_ext_alt_text":"true",
		"include_reply_count":"1",
		"tweet_mode":"extended",
		"include_entities":"true",
		"include_user_entities":"true",
		"include_ext_media_color":"true",
		"include_ext_media_availability":"true",
		"send_error_codes":"true",
		"simple_quoted_tweets":"true",
		"include_tweet_replies":"false",
		"ext":"mediaStats%2ChighlightedLabel%2CcameraMoment",
		"count":"20"
	}
	headers = {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"
            # "x-guest-token": "1200703472154206208"
	}
	def __init__(self,username):
		self.username = username
		# self.parse_pinned_tweet = True
		twitter_api.get_token()
		self.set_userId()

	#Set the number of tweets for each requests
	def set_count(self,count):
		self.params['count'] = str(count)

	# Get the user id for the profile 
	def set_userId(self):
		profile_url = "https://api.twitter.com/graphql/G6Lk7nZ6eEKd7LBBZw9MYw/UserByScreenName?variables=%7B%22screen_name%22%3A%22{}%22%2C%22withHighlightedLabel%22%3Atrue%7D".format(self.username)
		self.url_requests(profile_url)
		self.user_id = self.data['data']['user']['rest_id']
		pinned_tweet = self.data['data']['user']['legacy']['pinned_tweet_ids_str']
		# get the pinned tweet id
		self.pinned_tweet_id = pinned_tweet[0] if pinned_tweet else ''
		# if self.pinned_tweet_id == '':
		# 	self.parse_pinned_tweet = False

	#Request to the url and return json data
	def url_requests(self,url):
		req = requests.get(url,headers=self.headers)
		self.data = json.loads(req.text)

	def set_timeline(self):
		timeline = self.data['timeline']['instructions'][0]['addEntries']['entries']
		del timeline[-2:]
		for index,item in enumerate(timeline):
			if 'tweet' not in item['entryId']:
				timeline.pop(index)
				break
		self.timeline = timeline

	def parse_tweet_info(self):
		tweet_list = {}
		retweet_list = {}
		all_tweets = self.data['globalObjects']['tweets']
		if self.pinned_tweet_id != "":
			self.pinned_tweet = parser(all_tweets[self.pinned_tweet_id])
		for item in self.timeline:
			tweet_id = item['sortIndex']
			tweet_item = parser(all_tweets[tweet_id])
			tweet_list[tweet_id]=tweet_item
			if tweet_item.retweet_id != "":
				retweet_id = tweet_item.retweet_id
				retweet_item = parser(all_tweets[retweet_id])
				retweet_list[retweet_id] = retweet_item
		self.tweet_list = tweet_list
		self.retweet_list = retweet_list

	def find_last_cursor(self):
		last_cursor = self.data['timeline']['instructions'][0]['addEntries']['entries'][-1]['content']['operation']['cursor']['value']
		last_cursor = last_cursor.replace("+","%2B").replace("=","%3D")
		self.params['cursor']=last_cursor
		return last_cursor

	#Get the new cursor and fetch the next page
	def fetch(self,count):
		self.set_count(count)
		self.url_requests(self.requests_str)
		self.find_last_cursor()
		self.set_timeline()
		self.parse_tweet_info()

	def print_tweet(self,include_rts=True):
		for tweet_id,tweet in self.tweet_list.items():
			if (not include_rts) and (tweet.retweet_id != ""):
				continue
			print("{}\n{}\n---------------------------".format(str(tweet.id),tweet.full_text))

	def get_tweet_media(self,type='all',include_rts=True):
		media_list=[]
		for tweet_id,tweet in self.tweet_list.items():
			if (not include_rts) and (tweet.retweet_id != ""):
				continue
			if (tweet.retweet_id != ""):
				media_info = self.retweet_list[tweet.retweet_id].media_info(type)
			else:
				media_info = tweet.media_info(type)
			media_list.extend(media_info)
		return media_list

	#get the guess token for App
	@classmethod
	def get_token(cls):
		req = requests.post(('https://api.twitter.com/1.1/guest/activate.json'),headers = cls.headers)
		token_js = json.loads(req.text)
		cls.headers['x-guest-token']=token_js['guest_token']

	#get the requests string
	@property
	def requests_str(self):
		base_url = "https://api.twitter.com/2/timeline/profile/{}.json?".format(self.user_id)
		return base_url+'&'.join('{}={}'.format(key,value) for key,value in self.params.items())

class parser:
	def __init__(self,info):
		self.info = info

	def media_info(self,type):
		target_type_list=['photo','video','animated_gif'] if type=='all' else [type]
		media_list =[]
		if 'extended_entities' not in self.info.keys():
			return []
		all_media = self.info['extended_entities']['media']
		for index,media in enumerate(all_media):
			if media['type'] not in target_type_list:
				continue
			media_info = {}
			ext_dict = {
				'photo':'jpg',
				'video':'mp4',
				'animated_gif':'mp4'
			}
			#create media file name with format tweet_id.type
			post_fix = "_{}".format(index) if index>0 else ''
			ext = ".{}".format(ext_dict[media['type']])
			media_name = "{}{}{}".format(self.id,post_fix,ext)
			media_w = media['original_info']['width']
			media_h = media['original_info']['height']
			if media['type'] == 'photo':
				media_url = media['media_url_https'].replace('.jpg','?format=jpg&name=4096x4096')
			else:
				variants = media['video_info']['variants']
				bitrate = 0
				for item in variants:
					if 'bitrate' in item.keys():
						if item['bitrate'] >= bitrate:
							bitrate = item['bitrate']
							media_url = item['url']
			media_info['type'] = media['type']
			media_info['url'] = media_url
			media_info['name'] = media_name
			media_info['size'] = {'w':media_w,'h':media_h}
			media_list.append(media_info)
		return media_list

	@property
	def retweet_id(self):
		return self.info['retweeted_status_id_str'] if ('retweeted_status_id_str' in self.info.keys()) else ''

	@property
	def full_text(self):
		return self.info['full_text']

	@property
	def created_date(self):
		date_string = self.info['created_at']
		return time.strptime(date_string,'%a %b %d %H:%M:%S +0000 %Y')

	@property
	def id(self):
		return self.info['id_str']

def write_tweet(user,file,limit=None,include_rts=True,time_range=None):
	if time_range:
		start_time,end_time = time_range
	else:
		start_time = time.gmtime(0)
		end_time = time.gmtime()
	App = twitter_api(user)
	page_size = 20
	count = page_size
	if App.pinned_tweet_id != "":
		count = page_size + 1
		App.fetch(1)
		if (start_time<App.pinned_tweet.created_date<end_time):
			file.write("__PINNED__TWEET__\n")
			file.write("{}\n{}\n------------------------\n".format(App.pinned_tweet_id,App.pinned_tweet.full_text))
	remain = 20 if not limit else limit
	while True:
		if remain <= 20:
			count = remain if App.pinned_tweet_id == "" else remain+1
		App.fetch(count)
		for tweet_id,tweet in App.tweet_list.items():
			if (not include_rts) and (tweet.retweet_id != ""):
				continue
			if (tweet.created_date<start_time):
				return
			if not (tweet.created_date<end_time):
				continue
			print('Writing {}'.format(tweet.id))
			file.write("{}\n".format(time.asctime(tweet.created_date)))
			file.write("{}\n{}\n---------------------------\n".format(str(tweet.id),tweet.full_text))
		remain = remain - page_size if remain > 20 else 0
		if not limit:
			remain = 20
		if remain <= 0 or len(App.timeline)==0:
			break

def download_media(user,folder,type='photo',limit=None,include_rts=True,time_range=None):
	if time_range:
		start_time,end_time = time_range
	else:
		start_time = time.gmtime(0)
		end_time = time.gmtime()
	App = twitter_api(user)
	page_size = 20
	count = page_size
	if App.pinned_tweet_id != "":
		count = page_size + 1
		App.fetch(1)
		if (start_time<App.pinned_tweet.created_date<end_time):
			media_info = App.pinned_tweet.media_info(type)
			download([item for item in media_info],folder)
	remain = 20 if not limit else limit

	thread=[]
	i=0
	while True:
		# thread=[]
		# i=0
		if remain <= 20:
			count = remain if App.pinned_tweet_id == "" else remain+1
		App.fetch(count)
		media_list = []
		for tweet_id,tweet in App.tweet_list.items():
			if (not include_rts) and (tweet.retweet_id != ""):
				continue
			if (tweet.created_date<start_time):
				return
			if not (tweet.created_date<end_time):
				continue
			if tweet.retweet_id != "":
				media_info = App.retweet_list[tweet.retweet_id].media_info(type)
			else:
				media_info = tweet.media_info(type)
			media_list.extend(media_info)
		# thread_download(media_list,folder,4)
		# thread download
		if i<4:
			t = threading.Thread(target = thread_download,args=(media_list,folder,4))
			thread.append(t)
			t.start()
			i+=1
		if i==4:
			for t in thread:
				t.join()
			i=0
			thread=[]

		remain = remain - page_size if remain > 20 else 0
		if not limit:
			remain = 20
		if remain <= 0 or len(App.timeline)==0:
			break


#example
#download_media("donald_trump",folder = "D:\\Programing\\Python\\photo",limit=200)


