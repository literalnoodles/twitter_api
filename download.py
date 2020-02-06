import threading
import requests
from pathlib import Path

def download(tweet_list,folder):
    headers ={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"
    }
    for item in tweet_list:
        req = requests.get(item['url'],headers=headers)
        path = Path(folder)/item['name']
        print("Downloading file into {}".format(path))
        f = open(path,'wb')
        f.write(req.content)
        f.close()
# def download(tweet_list,folder):
# 	headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"}
# 	for item in tweet_list:
#         req = requests.get(item['url'],headers = headers)
#         path = Path(folder)/item['name']
#         print("Downloading file into {}".format(path))
#         f = open(path,'wb')
#         f.write(req.content)
#         f.close()
def thread_download(tweet_list,folder,workers):
    downloadThreads=[]
    n_work = len(tweet_list)
    workload = n_work//workers+1
    i=0
    while(i<n_work):
        downloadThread = threading.Thread(target = download,args=(tweet_list[slice(i,i+workload)],folder))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        i+=workload
    for downloadThread in downloadThreads:
        downloadThread.join()


# def download(url_dict,folder):
# 	headers = {
# 		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"
# 	}
# 	for filename,url in url_dict.items():
# 		req = requests.get(url,headers = headers)
# 		path = "{}\\{}".format(folder,filename)
# 		print("Downloading file into {}".format(path))
# 		f = open(path,'wb')
# 		f.write(req.content)
# 		f.close()

    #print(lst[slice(i,(n_work))])
# def thread_download(url_dict,folder,workers):
# 	downloadThreads=[]
# 	#n_work is the total number of tweets
# 	n_work = len(url_dict)
# 	#workload is the number of tweets for each worker
# 	workload = n_work//workers+1
# 	work_list=[{}]
# 	i=0
# 	j=0
# 	for filename, url in url_dict.items():
# 		if (i==workload):
# 			work_list.append({})
# 			j+=1
# 			i=0
# 		work_list[j][filename]=url
# 		i+=1
# 	for work_item in work_list:
# 		downloadThread = threading.Thread(target=download,args=(work_item,folder))
# 		downloadThreads.append(downloadThread)
# 		downloadThread.start()
# 	for downloadThread in downloadThreads:
# 		downloadThread.join()

