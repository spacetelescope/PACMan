#!/usr/bin/env python
import os,sys,pdb,scipy,glob
from pylab import *
from strolger_util import util as u

cwd = os.getcwd()
pacman_directory = os.path.join('/',*cwd.split('/')[:-1])
sys.path.append(pacman_directory)
sys.path.append(cwd)

# open source packages
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import cross_val_score, train_test_split

# custom packages that are all in the github repo
import pacman2020
from pacman2020 import PACManTrain, PACManPipeline
from utils.proposal_scraper import HSTProposalScraper
from utils.analyzer import PACManAnalyze



if __name__=='__main__':

    modelfile = 'strolger_pacman_model_7cycles.joblib' ###CONFIG
    
    ## Now loading in the test cycle
    pacman_scraper = HSTProposalScraper(for_training=False, cycles_to_analyze=[29]) ###CONFIG
    pacman_scraper.scrape_cycles()

    pacman_pipeline = PACManPipeline(cycle=29, model_name=modelfile) ###CONFIG
    pacman_pipeline.read_unclassified_data()#N=30)
    pacman_pipeline.load_model()
    
    pacman_pipeline.apply_model(pacman_pipeline.proposal_data["cycle_29"], training=False) ###CONFIG
    pacman_pipeline.model_results.info()
    pdb.set_trace()
    
    outfile = modelfile.split('.joblib')[0]+'.txt'
    if not os.path.isfile(cwd+'/model_results/production/'+outfile):
        pacman_pipeline.save_model_results(fout=outfile,training=False)
        print('Results written to model_results/production/'+modelfile.split('.joblib')[0]+'.txt')
    else:
        print('%s exists, exiting without overwriting...' %outfile)
        
    
