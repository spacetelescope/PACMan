#!/usr/bin/env python
import os,sys,pdb,scipy,glob
from pylab import *
from strolger_util import util as u

filename = sys.argv[1]
f = open(filename,'r')
lines = f.readlines()[1:]
f.close()
data = []
for line in lines:
    c = line.split(',')
    data.append(c[1])
print(sort(list(set(data))))
print(len(set(data)))

