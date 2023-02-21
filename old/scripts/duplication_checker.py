#!/usr/bin/env python
'''
./duplication_checker.py [--newcycles] cycle_number

More documentation to come...

'''

import os,sys,pdb,scipy,glob
from pylab import array, concatenate, where, savetxt
from fingerprint import Fingerprint
import string, re, getopt
import pickle

import multiprocessing
from functools import partial
import time


cwd = os.getcwd()
pacman_directory = os.path.join('/',*cwd.split('/')[:-1])
sys.path.append(pacman_directory)
sys.path.append(cwd)


def merge_dicts(*dict_args):
    result={}
    for dict in dict_args:
        result.update(dict)
    return (result)

def scrape_proposals(cycles):
    ## if new scraped texts are needed...
    from utils.proposal_scraper import HSTProposalScraper
    pacman_scraper = HSTProposalScraper(
        for_training=True,
        cycles_to_analyze=pastcycles,
        )
    pacman_scraper.scrape_cycles()
    return()

def hash_checker(key, hashtmp, hashdict):
    tmp=[]
    for k2, v2 in hashdict.items():
        ii = len(set(hashtmp[key][:,0])&set(v2[:,0]))
        tmp.append([key,k2,ii])
    return(tmp)



def main():
    verbose = True
    newcycles = False
    newcorpora = False
    
    try:
        opt,arg = getopt.getopt(
            sys.argv[1:],'v,h',
            longopts=['verbose','newcycles','newtext'])
        
    except getopt.GetoptError:
        print('Error : incorrect option or missing argument.')
        print(__doc__)
        sys.exit(1)
    for o, a in opt:
        if o in ['-h','--help']:
            print(__doc__)
            return(0)
        elif o in ['-v','--verbose']:
            verbose = True
        elif o == '--newcycles':
            newcycles = True
        elif o == '--newtext':
            newcorpora = True
    if len(arg) < 1:
        print(__doc__)
        print('\n Too few inputs.')
        print(arg)
        sys.exit(1)

    corpus = arg[0]
    duplications = run(corpus, newcycles=newcycles, newcorpora=newcorpora, verbose=verbose)
    return(duplications,corpus)
    
def run(corpus, newcycles=True, newcorpora=False, verbose=True, parallel=True, Nproc=12):
    #pastcycles = list(range(22,int(corpus)))
    pastcycles = list(range(22,29))
    pastcycles = [1]+pastcycles+[98,99]
    #pdb.set_trace()
    ### if new scraped texts are needed...
    ## scrape_proposals(pastcycles)

    ## settting up a hashdict to compare to...
    hashdict={}
    fp = Fingerprint(kgram_len=7, window_len=12)

    print ('Checking against hash library')
    pastcycles.reverse()

    for cycle in pastcycles:
        # check first if the hashes exist already 
        outfile = 'cycle%02d_hashes.pkl' %cycle
        outfile = cwd+'/duplication_hashes/'+outfile
        if os.path.isfile(outfile):
            if verbose: print ('loading on %s' %(outfile))
            hashtmp=pickle.load(open(outfile,'rb'))
        else:
            propdir = cwd+'/training_data/training_corpus_cy%02d'%cycle
            if not os.path.isdir(propdir): continue
            if verbose:
                print('no hash volume for cycle %02d, building from proposals...' %cycle)
                print('working on proposals in %s' %propdir)
                print('to make %s' %outfile)
            hashtmp={}
            for proposal in glob.glob(propdir+'/*training.txt'):
                nkey =  int(proposal.split('/')[-2][-2:])*10000+int(os.path.basename(proposal)[:4])
                with open(proposal, 'r') as fobj:
                    lines = fobj.readlines()
                    text = [line.strip('\n') for line in lines]
                hashtmp[nkey]=array(fp.generate(text))
            pickle.dump(hashtmp,open(outfile,'wb'))
        hashdict = merge_dicts(hashdict,hashtmp)

    if newcycles:
        cycle = int(corpus)
        outfile = 'cycle%02d_hashes.pkl' %cycle
        outfile = cwd+'/duplication_hashes/'+outfile
        if os.path.isfile(outfile):
            if verbose: print ('loading on %s' %(outfile))
            hashtmp=pickle.load(open(outfile,'rb'))
        else:
            propdir = cwd+'/training_data/training_corpus_cy%02d'%cycle
            #propdir = cwd+'/proposal_data/Cy%02d_proposals_txt'%cycle
            if verbose:
                print('no hash volume for cycle %02d, building from proposals...' %cycle)
                print('working on proposals in %s' %propdir)
                print('to make %s' %outfile)
            hashtmp={}
            for proposal in glob.glob(propdir+'/*training.txt'):
                nkey =  int(proposal.split('/')[-2][-2:])*10000+int(os.path.basename(proposal)[:5])
            ## for proposal in glob.glob(propdir+'/*.txtx'):
            ##     nkey =  int(proposal.split('/')[-2][2:4])*10000+int(os.path.basename(proposal)[:4])
                with open(proposal, 'r') as fobj:
                    lines = fobj.readlines()
                    text = [line.strip('\n') for line in lines]
                hashtmp[nkey]=array(fp.generate(text))
            pickle.dump(hashtmp,open(outfile,'wb'))
    else:
        if not os.path.isfile(corpus):
            print ("No file %s found" %(corpus))
            sys.exit(1)
        nkey = 0
        with open(corpus, 'r') as fobj:
            lines = fobj.readlines()
            text = [line.strip('\n') for line in lines]
        hashtmp[nkey]=array(fp.generate(text))       

    start_time = time.time()
    if parallel:
        if verbose: print('... running hash checking in parallel')
        run_hash_chk = partial(hash_checker,hashtmp=hashtmp,hashdict=hashdict)
        pool = multiprocessing.Pool(processes=Nproc)
        result = pool.map(run_hash_chk, list(hashtmp.keys()))
        pool.close()
        for item in result:
            item = array(item)
            try:
                outinfo=concatenate((outinfo,item),axis=0)
            except:
                outinfo = item
        
    else:
        outinfo = []
        for key in hashtmp.keys():
            print(key)
            tmp = hash_checker(key, hashtmp, hashdict)
            tmp = array(tmp)

            try:
                outinfo = concatenate((outinfo,tmp),axis=0)
            except:
                outinfo = tmp
            print()
    if verbose: print('processing time = %2.1f seconds' %(time.time() - start_time))
    print('Done')
    return(outinfo)
    

if __name__=='__main__':

    duplications, corpus = main()
    pdb.set_trace()
    idx = where(duplications[:,2] > 10)
    savetxt('Cycle%02d_duplications.txt' %(int(corpus)),duplications[idx],fmt='%s')
    print ("... Duplications written to Cycle%02d_duplications.txt" %(int(corpus)))
    
