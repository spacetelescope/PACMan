#!/usr/bin/env python
import os,sys,pdb,scipy,glob,pickle
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

    loadmodel = True
    loadfile = True
    
    savefile = cwd+'/store/saved_corpora.pkl'
    modelfile = 'strolger_pacman_model_6cycles.joblib'

    if not loadmodel or not os.path.isfile('models/'+modelfile):
        if os.path.isfile(savefile) and loadfile:
            print('-'*58)
            print('Loading %s' %savefile)
            pacman_training=pickle.load(open(savefile,'rb'))

        else:
            print('-'*58)
            print('Creating %s' %savefile)

            if os.path.isfile(savefile): os.remove(savefile)
            # Make an instance of the proposal scraping and scrape each cycle
            pacman_scraper = HSTProposalScraper(for_training=True, cycles_to_analyze=[22, 23, 24, 25, 26, 27])
            pacman_scraper.scrape_cycles()

            # Now lets store a training set...
            pacman_training = PACManTrain(cycles_to_analyze=[22, 23, 24, 25, 26, 27])
            pacman_training.read_training_data(parallel=False)
            pickle.dump(pacman_training,open(savefile,'wb'))


        # Checking the proposal information...
        print('Found proposal information for:\n'+'\n'.join(pacman_training.proposal_data.keys())+'\n')
        # Print the first 5 rows of the DataFrame for each cycle
        for key in pacman_training.proposal_data.keys():
            print(f"Displaying some information for {key}...")
            print(pacman_training.proposal_data[key].info())
            print('-'*58)


        # Now actual training...
        dft=pd.DataFrame([])
        for dfn in pacman_training.proposal_data.keys():
            dft=dft.append(pacman_training.proposal_data[dfn], sort=True)
        pacman_training.fit_model(df=dft)
        print(pacman_training.model)

        ## saving training...
        if os.path.isfile('models/'+modelfile):
            print('removing %s'%modelfile)
            os.remove('models/'+modelfile)
        print('saving %s'%modelfile)
        pacman_training.save_model(fname=modelfile)

    
    ## Now loading in the test cycle
    pacman_scraper = HSTProposalScraper(for_training=False, cycles_to_analyze=[28])
    pacman_scraper.scrape_cycles()

    ## apply saved model
    pacman_pipeline = PACManPipeline(cycle=28, model_name=modelfile)
    pacman_pipeline.read_unclassified_data()#N=30)
    pacman_pipeline.load_model()
    
    pacman_pipeline.apply_model(pacman_pipeline.proposal_data["cycle_28"], training=False)
    pacman_pipeline.model_results.info()
    
    pacman_pipeline.save_model_results(fout=modelfile.split('.joblib')[0]+'.txt',training=False)
    print('Results written to model_results/production/'+modelfile.split('.joblib')[0]+'.txt')
    
    
