#!/usr/bin/env python
import os,sys,pdb,scipy,glob,pickle
from pylab import *
from strolger_util import util as u



if __name__=='__main__':

    
    #rankings = pickle.load(open('HST_C28_midcycle1_Panelists_matches.pkl','rb'))
    #rankings = pickle.load(open('HST_C28_midcycle1_Panelists_match_check.pkl','rb'))
    #conflicts = pickle.load(open('HST_C28_midcycle1_Panelists_conflicts.pkl','rb'))

    #rankings = pickle.load(open('JWST_C01_Panelists_match_check.pkl','rb'))
    #conflicts= pickle.load(open('JWST_C01_Panelists_conflicts.pkl','rb'))
    #outfile = 'JWST_C01_assignments.txt'

    rankings = pickle.load(open('HST_C30_panelists_match_check.pkl','rb'))
    conflicts= pickle.load(open('HST_C29_panelists_conflicts.pkl','rb'))
    outfile = 'HST_C29_1_assignments.txt'


    if os.path.isfile(outfile): os.remove(outfile)
    f = open(outfile,'w')
    new_dict={}
    files = glob.glob('unclassified_proposals/corpus_cy30/*_training.txt')
    f.write('#proposal_number, recommended_reviewer, cs_score, conflicts(name, num_proposals)\n')
    for file in sorted(files):
        tmp = []
        proposal = int(os.path.basename(file)[:5])
        for reviewer in rankings.keys():
            idx = where(rankings[reviewer][:,0]==proposal)
            try:
                tmp.append([reviewer, float(rankings[reviewer][idx[0],1])])
            except:
                pdb.set_trace()
        tmp=array(tmp)
        tmp=tmp[tmp[:,1].argsort()[::-1]]
        new_dict[proposal]=tmp
        for reviewer in tmp[:6]: # number here controls the number of top recommneded reviewers
            f.write('%s, "%s", %.2f, '%(proposal, reviewer[0],float(reviewer[1])))
            close_conflicts = sorted(conflicts[reviewer[0]].items(),
                                     key=lambda x: [x[1],x[0]], reverse=True)
            f.write('"')
            for cc,npub in close_conflicts:
                f.write('%s, %d, '%(cc,int(npub)))
            f.write('"')
            f.write('\n')
        f.write('\n')
    f.close()
    
        


        
    
