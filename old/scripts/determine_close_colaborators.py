#!/usr/bin/env python
import os,sys,pdb,scipy,glob,pickle
from pylab import *
from strolger_util import util as u
import datetime, random

cwd = os.getcwd()
pacman_directory = os.path.join('/',*cwd.split('/')[:-1])
sys.path.append(pacman_directory)
sys.path.append(cwd)

# open source packages
## import ads.sandbox as ads
import ads
import pandas as pd
import re
from collections import defaultdict, Counter

from categorize_ads_reviewers import author_query

def anyCollaborators(papers):
    '''
    any author in the last 3-years
    create a list of collaborators in refereed papers
    '''

    this_year = datetime.date.today().year
    collaborators={}
    for author in papers.keys():
        tmp = []
        for paper in papers[author]:
            if ((this_year - int(paper.year))<=3.):
                tmp+=paper.author
        newlist=[]
        for item in tmp:
            try:
                newlist.append(item.split(',')[0]+', '+item.split(',')[1][1]+'.')
            except:
                newlist.append(item)
        collaborators[author]=sorted(set(newlist))
    return(collaborators)

def frequentCollaborators(papers, n=3, pis=None):
    '''
    any author in the last 3-years
    published 3 or more times together
    create a list of collaborators in refereed papers
    '''

    this_year = datetime.date.today().year
    collaborators={}
    for author in papers.keys():
        tmp = []
        for paper in papers[author]:
            if ((this_year - int(paper.year))<=n):
                if pis:
                    tmp+=paper.author[:pis]
                else:
                    tmp+=paper.author
        newlist=[]
        for item in tmp:
            try:
                newlist.append(item.split(',')[0]+', '+item.split(',')[1][1]+'.')
            except:
                newlist.append(item)
        counts = Counter(newlist)
        hicounts =  Counter({k: c for k, c in counts.items() if c >=3})
        collaborators[author]={k: c for k, c in hicounts.items()}
    return(collaborators)
    

if __name__=='__main__':


    force = False

    this_year = datetime.date.today().year
    #authorfile = 'AAS_full_membs_for_NASA.csv'
    #authorfile = 'HST_C28_midcycle1_Panelists.csv'
    #authorfile = 'JWST_C01_Panelists.csv'
    authorfile = 'HST_C29_panelists.csv'
    authorpkl = authorfile.replace('.csv','.pkl')
    querypkl = authorfile.replace('.csv','_querry.pkl')
    outfile = authorfile.replace('.csv','_conflicts.pkl')

    if not os.path.isfile(querypkl) or force:
        author_list = pd.read_csv(authorfile,header=0)
        author_keys = [x.lower() for x in list(author_list.keys())]
        author_list.columns=author_keys
        if 'last_name' in author_keys:
            authors = [i+','+j for i, j in zip(author_list.last_name,author_list.first_name)]
        else:
            authors = author_list.name
        ## authors=random.choices(authors,k=200) ## for testing a random set of 200 
        ## authors=['Strolger, L.', 'Gordon, K.'] ## for coi
        ads_df, papers = author_query(authors)
        if force:
            os.remove(authorpkl)
            os.remove(querypkl)
        ads_df.to_pickle(authorpkl)
        pickle.dump(papers,open(querypkl,'wb'))
    else:
        ads_df = pickle.load(open(authorpkl,'rb'))
        papers = pickle.load(open(querypkl,'rb'))


    if not os.path.isfile(outfile) or force:
        ## collaborator_dict = anyCollaborators(papers) ## not as elegant
        ## collaborator_dict = frequentCollaborators(papers, n=1)
        ## collaborator_dict = frequentCollaborators(papers, n=3)
        ## pdb.set_trace()
        collaborator_dict = frequentCollaborators(papers, n=3, pis=3)
        pickle.dump(collaborator_dict, open(outfile,'wb'))
    else:
        print(outfile,' already exists... exiting')
        
    

    
                

    


    
    
