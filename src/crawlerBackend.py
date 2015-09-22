#!\Python27\python.exe
import zerorpc
import urllib2
import os
import re
import sys
import time
import glob
from urllib2 import Request, urlopen, URLError, HTTPError
from lxml import etree
from io import StringIO, BytesIO

class Crawler(object):
	# --- | globals | ---------------------------------+
	bpLinearDNA = 3800000
	retMax = '100'
	retStart = '0'

	#TODO: Create python socket.io client to communicate with html view.
	#      Every print shall be a message from here via node.js server
	#      to the html view. The node.js server is already prepared.

	def crawl(self, searchString):
		retMax = Crawler.retMax
		retStart = Crawler.retStart
		bpLinearDNA = Crawler.bpLinearDNA
		searchString = re.sub(r"[^\w\s]", '', searchString) # remove all non-word characters (everything except numbers and letters)
		searchString = re.sub(r"\s+", '+', searchString) # replace all runs of whitespace with a plus
		path = self.createFolder(searchString)

		elementArray = []
		# --- get all the IDs/Gis for the search string
		while True:
			url_esearch = self.esearchUrlBuilder(retStart, retMax, searchString)
			xmlroot = etree.XML(self.sendRequest(url_esearch)) #.XML() returns root node, .fromstring() as well
			count = int(xmlroot.find('Count').text)
			#print retStart, retMax, count

			for xmlchilds in xmlroot.iter('Id'):
				elementArray.append(xmlchilds.text)
			
			retStart = int(retStart)
			retMax = int(retMax)
			retStart += retMax
			if retStart > count:
				retStart = count

			print '%d datasets of %d for further processing downloaded' %(retStart, count)

			if(retStart == count):
				break
				#return 'RPC Backend: %d datasets of %d for further processing downloaded' %(retStart, count)

		begin = 0
		until = retMax
		fragmentedArray = []
		while True:
			#print 'range: %d' %(len(elementArray))
			for i in range(begin, until):
				#print 'iter inner loop %d: %s' %(i, elementArray[i])
				fragmentedArray.append(elementArray[i])
			begin += retMax
			until += retMax
			if until >= len(elementArray):
				until = len(elementArray)

			# --- build the ncbi esummary url request with the ids and send it
			url_esummary = self.esummaryUrlBuilder(fragmentedArray)
			xmlroot = etree.XML(self.sendRequest(url_esummary))

			# --- searching for 'bp linear DNA' values
			# --- in xml output it's attribute 'Length'
			del fragmentedArray[:]
			for xmlchilds in xmlroot.iter('Item'):
				if xmlchilds.get('Name') == 'Gi':
					fragmentedArray.append(xmlchilds.text)
				if xmlchilds.get('Name') == 'Length':
					if int(xmlchilds.text) < bpLinearDNA:
						fragmentedArray.pop()

			if len(fragmentedArray) > 0:
				# --- fetching fasta data
				url_efetch = self.efetchUrlBuilder(fragmentedArray)
				print 'url fetch: %s' %url_efetch
				del fragmentedArray[:]

				if os.path.exists(path+searchString+'.fasta'):
					if os.path.getsize(path+searchString+'.fasta') > 100000000000:
						tmpFiller = str(begin)
						with open(path+searchString+'_'+tmpFiller+'.fasta', 'ab') as f:
							f.write(self.sendRequest(url_efetch))
					else:
						with open(path+searchString+'.fasta', 'ab') as f:
							f.write(self.sendRequest(url_efetch))
				else:
					with open(path+searchString+'.fasta', 'w') as f:
						f.write(self.sendRequest(url_efetch))

			if begin > len(elementArray):
				break
				#return 'RPC Backend: %d datasets of %d for further processing downloaded' %(retStart, count)
				print 'finish'
				return "Python Backend finished processing."

	def esearchUrlBuilder(self, retStart, retMax, searchString):
		str(retStart)
		url_esearch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term='+searchString+'&retmax=%s&retstart=%s' %(retMax, retStart)
		#url_esearch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term=Xanthomonas+albilineans&retmax=%s&retstart=%s' %(retMax, retStart)
		return url_esearch

	def esummaryUrlBuilder(self, fragmentedArray):
		url_esummary = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=nuccore&id='
		url_esummary += ','.join(fragmentedArray) #appending transformed string to url
		return url_esummary

	def efetchUrlBuilder(self, fragmentedArray):
		url_efetch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&rettype=fasta&retmode=text&id='
		url_efetch += ','.join(fragmentedArray)
		return url_efetch

	# --- HTTP request - response to get XML
	def sendRequest(self, url):
		req = urllib2.Request(url)
		retries = 1
		established = False
		while not established:
			try:
				response = urllib2.urlopen(req)
				established = True
			except HTTPError as e:
				print 'The server couldn\'t handle the request.'
				print 'Error code: ', e.code
				waiting(retries)
				retries += 1
			except URLError as e:
				print 'Failed to reach a server.'
				print 'Reason: ', e.reason
				waiting(retries)
				retries += 1
			time.sleep(1)
		page = response.read()
		return page

	def waiting(retries):
		print "%s. retry attempt..." %retries
		wait = retries * 2
		if wait > 60:
			wait = 60
		time.sleep(wait)

	def createFolder(self, searchString):
		#timestamp = time.strftime("%Y%m%d-%H:%M:%S")
		#path = '../fasta/'+searchString+'_'+timestamp+'/'
		path = '../fasta/'+searchString+'/'
		print 'Fasta files downloading to: %s' %(path)
		try: 
		    os.makedirs(path)
		except OSError:
		    if not os.path.isdir(path):
		    	raise

		# --- clear output files in folder
		# TODO: ?ask user whether he wants to delete all files?
		#       and transfer it to createFolder()
		filelist = glob.glob(path+'*.fasta')
		for f in filelist:
			os.remove(f)
		return path

s = zerorpc.Server(Crawler())
s.bind("tcp://0.0.0.0:4242")
s.run()