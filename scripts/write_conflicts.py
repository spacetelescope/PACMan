#!/usr/bin/env python
import os,sys,pdb,scipy,glob,pickle
from pylab import *
from strolger_util import util as u

if __name__=='__main__':


    #file = 'JWST_C01_Panelists_conflicts.pkl'
    file = 'HST_C29_panelists_conflicts.pkl'
    data = pickle.load(open(file,'rb'))
    outfile = file.replace('pkl','txt')
    f = open(outfile,'w')
    for k in sorted(data.keys()):
        odict = dict(sorted(data[k].items(), key=lambda item: item[1],reverse=True))
        print('%s-> %s' %(k,odict))
        f.write('%s-> \t %s\n' %(k,odict))
    f.close()
    
        
