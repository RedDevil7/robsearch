#!/usr/bin/python
#coding: utf-8

import urlparse
import re
import sys
import cPickle
from time import strftime, localtime
from urllib2 import urlopen
from threading import Thread, Event, RLock
from BeautifulSoup import BeautifulSoup as be
from Queue import PriorityQueue, Empty
from simpleflock import SimpleFlock

class Crawler:
	def __init__(self, domainsPath, initialLinks):
		self.visited = set()
		self.queue = PriorityQueue()
		self.stopped = Event()
		self.lock = RLock()
		self.accept = re.compile('http://.+\.pl/')
		self.reject = re.compile('^.*\.(png|jpg|jpeg|gif|css|js|ico|mp3|wav|swf|jar|java|dat|txt|doc|pdf|zip|7z|tar|rar|gz)$', re.I)

		for link in initialLinks:
			self.queue.put(((0, 0), link))
		self.domainsPath = domainsPath
		self.loadDomains()

		self.work()

	def work(self):
		self.workers = []
		for i in xrange(1, 16):
			worker = Worker(self, i)
			worker.start()
			self.workers.append(worker)
		try:
			i = 0
			while not self.stopped.is_set():
				self.stopped.wait(1)
				i += 1
				if i > 300:
					i = 0
					with self.lock:
						self.saveDomains()
		except KeyboardInterrupt:
			self.stopped.set()

		self.debug('Exiting')

		#for worker in self.workers:
		#	worker.join()
		with self.lock:
			self.saveDomains()

	def debug(self, msg):
		with self.lock:
			try:
				print >>sys.stderr, strftime('%Y-%m-%d %H:%M:%S', localtime()) + ' ' + str(msg).encode('utf-8')
			except:
				pass


	def loadDomains(self):
		with open(self.domainsPath, 'rb') as fh:
			self.domains = cPickle.load(fh)



	def saveDomains(self):
		with SimpleFlock(self.domainsPath + '.lock', 2):
			with open(self.domainsPath, 'wb') as fh:
				cPickle.dump(self.domains, fh, 2)



class Worker(Thread):
	def __init__(self, crawler, number):
		self.crawler = crawler
		self.number = number
		Thread.__init__(self)

	def run(self):
		while not self.crawler.stopped.is_set():
			try:
				priority, link = self.crawler.queue.get_nowait()
				priority, distance = priority
				self.crawler.debug('pri:%d, dis:%d::  %s' % (priority, distance, link))
				sys.stderr.flush()
			except Empty:
				self.crawler.stopped.wait(1)
				continue

			#download
			try:
				raw = urlopen(link, None, 5).read()
				try:
					content = raw.decode('utf-8')
				except UnicodeError as inst:
					content = raw
			except Exception as inst:
				self.crawler.debug(inst)
				continue

			try:
				soup = be(content)
			except Exception:
				self.crawler.debug('exception: beautifulsoup failed')
				continue
			try:
				index = 0
				subLinks = []
				for elem in soup.findAll('a', href=True):
					subLinks.append(urlparse.urljoin(link, elem.get('href')))
				for elem in soup.findAll('img', src=True):
					subLinks.append(urlparse.urljoin(link, elem.get('src')))
				for subLink in subLinks:
					subLink = re.sub('#.*$', '', subLink)
					subLink = subLink.lower()
					if not self.crawler.accept.match(subLink) or self.crawler.reject.match(subLink):
						continue
					if subLink in self.crawler.visited:
						continue
					index += 1
					domain = urlparse.urlparse(subLink)[1]
					with self.crawler.lock:
						self.crawler.visited.add(subLink)
						if domain not in self.crawler.domains:
							sys.stdout.flush()
							self.crawler.debug('new domain: ' + domain)
							self.crawler.domains[domain] = 1
						else:
							self.crawler.domains[domain] += 1
						priority = 0
						priority -= distance
						priority -= (25 + distance ** 2) / float(self.crawler.domains[domain])
						priority += index
					self.crawler.queue.put(((priority, distance + 1), subLink))
			except Exception as inst:
				self.crawler.debug('exception: ' + str(inst))
				continue

		self.crawler.debug('Thread ' + str(self.number) + ' ended')

if __name__ == '__main__':
	Crawler('domains.dat', sys.argv[1:])
