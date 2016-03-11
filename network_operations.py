import requests
import os

# Downloads page specified at url and saves at specified path
# Returns boolean on whether operation succeeded
# filePath should end in a "/"
def downloadPage(url=None, filePath="Crawled Pages/", fileName="newfile.txt"):
	try:
		if not os.path.exists(filePath):
			os.makedirs(filePath)
		r = requests.get(url)
		inputfile = open(filePath + fileName, "w+")
		inputfile.write(r.text.encode('utf-8'))
		inputfile.close()
		return True
	except Exception as e:
		print e
		return False