#!/usr/bin/env python
import os
import json
import logging

# custom packages that are all in the github repo
from scripts import constants as constants
from pacman_classes import PACManPipeline
from utils.proposal_scraper import ProposalScraper


def main():
    #configfile = "./config.json"
    #with open(configfile) as data_file:
    #    config = json.loads(data_file.read())
    config = constants.config

    modelfile = config['modelfile']
    cycle_number = config['main_test_cycle']
    #past_cycles = config['past_cycles']


    # Now loading in the test cycle
    pacman_scraper = ProposalScraper(for_training=False, cycles_to_analyze=[cycle_number])
    pacman_scraper.scrape_cycles()

    pacman_pipeline = PACManPipeline(cycle=cycle_number, model_name=modelfile)
    pacman_pipeline.read_unclassified_data()
    pacman_pipeline.load_model()

    pacman_pipeline.apply_model(pacman_pipeline.proposal_data[cycle_number], training=False)
    pacman_pipeline.model_results.info()

    outfile = modelfile.split('.joblib')[0]+'.txt'
    if not os.path.isfile(outfile):
        pacman_pipeline.save_model_results(fout=outfile, training=False)
        logging.info('Results written to '+outfile)
    else:
        logging.info('%s exists, exiting without overwriting...' % outfile)


if __name__ == '__main__':
    logging.info("Proceeding with categorize_one_cycle")
    main()
