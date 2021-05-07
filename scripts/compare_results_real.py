#!/usr/bin/env python
import os,sys,pdb,scipy,glob
from pylab import *
from strolger_util import util as u
import pandas as pd


file1 = sys.argv[1] #pacman
file2 = sys.argv[2] #hand

outfile = 'HST_C29_1_recategorization.txt'
f=open(outfile,'w')

f.write('#propid,pacman_cat,orig_cat,certainty\n')
data1 = pd.read_csv(file1)
data2 = pd.read_csv(file2)
for index1, row in data1.iterrows():
    propid = int(os.path.basename(row['fname']).split('.')[0].split('_')[0])
    cat1 = row['encoded_model_classification']
    cat1_n = row['model_classification']
    score1 = row[3+cat1]
    index2 = [idx for idx, s in enumerate(data2['proposal_num']) if propid == s][0]
    cat2 = data2['hand_classification'][index2]
    if cat1_n != cat2:
        #print(propid, index1, index2, cat1_n, cat2, score1)#, score2)
        print('%05d, \"%s\", \"%s\", %.2f' %(propid, cat1_n, cat2, score1))
        f.write('%05d, \"%s\", \"%s\", %.2f\n' %(propid, cat1_n, cat2, score1))
f.close()        
pdb.set_trace()
    


