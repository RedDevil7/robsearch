#!/usr/bin/python
import cPickle
from simpleflock import SimpleFlock

with SimpleFlock('domains.dat.lock', 2):
	with open('domains.dat', 'rb') as fh:
		data = cPickle.load(fh)
		for domain in data.keys():
			print domain.encode('utf-8')
