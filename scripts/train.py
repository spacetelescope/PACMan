#!/usr/bin/env python
import os
import pickle
import json
import pandas as pd
import logging

# custom packages that are all in the github repo
from pacman_classes import PACManTrain, PACManPipeline
from utils.proposal_scraper import ProposalScraper
from scripts import constants as constants
config = constants.config


def main():
    #configfile = "./config.json"
    #with open(configfile) as data_file:
    #    config = json.loads(data_file.read())

    loadmodel = True
    loadfile = True

    savefile = config['output_dir']+config['train_savefile']
    modelfile = config['modelfile']
    past_cycles = config['past_cycles']
    main_test_cycle = config['main_test_cycle']

    if not loadmodel or not os.path.isfile(config['models_dir']+modelfile):
        if os.path.isfile(savefile) and loadfile:
            logging.info('-'*58)
            logging.info('Loading %s' % savefile)
            pacman_training = pickle.load(open(savefile, 'rb'))

        else:
            logging.info('-'*58)
            logging.info('Creating %s' % savefile)

            if os.path.isfile(savefile):
                os.remove(savefile)
            # Make an instance of the proposal scraping and scrape each cycle
            pacman_scraper = ProposalScraper(for_training=True, cycles_to_analyze=past_cycles)
            pacman_scraper.scrape_cycles()

            # Now lets store a training set...
            pacman_training = PACManTrain(cycles_to_analyze=past_cycles)
            pacman_training.read_training_data(parallel=False)
            pickle.dump(pacman_training, open(savefile, 'wb'))

        # Checking the proposal information...
        logging.info('Found proposal information for:\n'+'\n'.join(pacman_training.proposal_data.keys())+'\n')
        # Print the first 5 rows of the DataFrame for each cycle
        for key in pacman_training.proposal_data.keys():
            logging.info(f"Displaying some information for {key}...")
            logging.info(pacman_training.proposal_data[key].info())
            logging.info('-'*58)

        # Now actual training...
        dft = pd.DataFrame([])
        for dfn in pacman_training.proposal_data.keys():
            dft = dft.append(pacman_training.proposal_data[dfn], sort=True)
        pacman_training.fit_model(df=dft)
        logging.info(pacman_training.model)

        # saving training...
        if os.path.isfile(config['models_dir'] + modelfile):
            logging.info('removing %s' % modelfile)
            os.remove(config['models_dir'] + modelfile)
        logging.info('saving %s' % modelfile)
        pacman_training.save_model(fname=modelfile)

    if config['test_training']=="true":
        # Now loading in the test cycle
        pacman_scraper = ProposalScraper(for_training=False, cycles_to_analyze=[main_test_cycle])
        pacman_scraper.scrape_cycles()

        # apply saved model
        pacman_pipeline = PACManPipeline(cycle=main_test_cycle, model_name=modelfile)
        pacman_pipeline.read_unclassified_data()
        pacman_pipeline.load_model()
        pacman_pipeline.apply_model(pacman_pipeline.proposal_data[main_test_cycle], training=False)
        pacman_pipeline.model_results.info()

        pacman_pipeline.save_model_results(fout=modelfile.split('.joblib')[0]+'.txt', training=False)
        logging.info('Results written to '+config['results_dir']+modelfile.split('.joblib')[0]+'.txt')


if __name__ == '__main__':
    logging.info("Proceeding with train_and_test")
    main()
