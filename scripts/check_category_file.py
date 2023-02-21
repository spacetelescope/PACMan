#!/usr/bin/env python
import sys
import logging


filename = sys.argv[1]
f = open(filename, 'r')
lines = f.readlines()[1:]
f.close()
data = []
for line in lines:
    c = line.split(',')
    data.append(c[1])
logging.info(sort(list(set(data))))
logging.info(len(set(data)))
