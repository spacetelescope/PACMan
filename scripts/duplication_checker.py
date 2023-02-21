#!/usr/bin/env python
'''
./duplication_checker.py [--newcycles] cycle_number

More documentation to come...

'''

from fingerprint import Fingerprint
from functools import partial
import glob
import json
import logging
import multiprocessing
import os
import pickle
from pylab import array, concatenate, where, savetxt
import sys
import time

from scripts import constants as constants
config = constants.config


def merge_dicts(*dict_args):
    result = {}
    for dict in dict_args:
        result.update(dict)
    return (result)


def scrape_proposals(cycles):
    # if new scraped texts are needed...
    from utils.proposal_scraper import ProposalScraper
    pacman_scraper = ProposalScraper(
        for_training=False,
        cycles_to_analyze=cycles,
        )
    pacman_scraper.scrape_cycles()
    return()


def hash_checker(key, hashtmp, hashdict):
    tmp = []
    for k2, v2 in hashdict.items():
        if key==k2:continue
        ii = len(set(hashtmp[key][:, 0]) & set(v2[:, 0]))
        tmp.append([key, k2, ii])
    return(tmp)


def main():
    if config['duplication_checker_newcycles'].lower() == 'true':
        newcycles = True
    else:
        newcycles = False

    corpus = config['main_test_cycle']#+config['duplication_checker_corpus_suffix']

    logging.info("Using corpus " + (corpus+constants.duplication_hashes_suffix))
    Nproc=multiprocessing.cpu_count()
    duplications = run(corpus, newcycles=newcycles, Nproc=Nproc)
    return(duplications, os.path.join(constants.path_duplication_hashes,
                        (corpus+constants.duplication_hashes_suffix)))


def run(corpus, newcycles=True, parallel=True, Nproc=12):
    pastcycles = config['past_cycles']
    logging.info("Using cycles" + str(pastcycles))


    if config['duplication_checker_need_new_texts'] == "true":
        scrape_proposals(pastcycles)

    # settting up a hashdict to compare to...
    hashdict = {}
    fp = Fingerprint(kgram_len=7, window_len=12)

    logging.info('Checking against hash library')
    pastcycles.reverse()

    for cycle in pastcycles:
        # check first if the hashes exist already
        outfile = os.path.join(constants.path_duplication_hashes,
                            (cycle+constants.duplication_hashes_suffix))
        if os.path.isfile(outfile):
            logging.info('loading on %s' % (outfile))
            hashtmp = pickle.load(open(outfile, 'rb'))
        else:
            propdir = os.path.join(constants.path_proposals_processed, cycle)
            if not os.path.isdir(propdir):
                continue
            logging.info('no hash volume for {}, building from proposals...'.format(cycle))
            logging.info('working on proposals in %s' % propdir)
            logging.info('to make %s' % outfile)
            hashtmp = {}
            for proposal in glob.glob(propdir+constants.training_suffix):
                nkey = int(os.path.dirname(proposal).split('/')[-1])*100000+int(os.path.basename(proposal)[:5])
                with open(proposal, 'r') as fobj:
                    lines = fobj.readlines()
                    text = [line.strip('\n') for line in lines]
                hashtmp[nkey] = array(fp.generate(text))
            pickle.dump(hashtmp, open(outfile, 'wb'))

        hashdict = merge_dicts(hashdict, hashtmp)
    if newcycles:
        cycle = corpus
        outfile = os.path.join(constants.path_duplication_hashes,
                            (cycle+constants.duplication_hashes_suffix))
        if os.path.isfile(outfile):
            logging.info('loading on %s' % (outfile))
            hashtmp = pickle.load(open(outfile, 'rb'))
        else:
            propdir = os.path.join(constants.path_proposals_processed, cycle)
            logging.info('no hash volume for {}, building from proposals...'.format(cycle))
            logging.info('working on proposals in %s' % propdir)
            logging.info('to make %s' % outfile)
            hashtmp = {}
            for proposal in glob.glob(propdir+constants.training_suffix):
                nkey = int(os.path.dirname(proposal).split('/')[-1])*100000+int(os.path.basename(proposal)[:5])
                with open(proposal, 'r') as fobj:
                    lines = fobj.readlines()
                    text = [line.strip('\n') for line in lines]
                hashtmp[nkey] = array(fp.generate(text))
            pickle.dump(hashtmp, open(outfile, 'wb'))
    else:
        filename = os.path.join(constants.duplication_hashes_dir,
                        (corpus+constants.duplication_hashes_suffix))
        if not os.path.isfile(filename):
            logging.info("No file %s found" % (filename))
            sys.exit(1)
        nkey = 0
        with open(filename, 'r', errors='replace') as fobj:
            lines = fobj.readlines()
            text = [line.strip('\n') for line in lines]
        hashtmp[nkey] = array(fp.generate(text))
        filename = None

    start_time = time.time()
    if parallel:
        logging.info('... running hash checking in parallel')
        run_hash_chk = partial(hash_checker, hashtmp=hashtmp, hashdict=hashdict)
        pool = multiprocessing.Pool(processes=Nproc)
        result = pool.map(run_hash_chk, list(hashtmp.keys()))
        pool.close()
        for item in result:
            item = array(item)
            try:
                outinfo = concatenate((outinfo, item), axis=0)
            except:
                outinfo = item

    else:
        outinfo = []
        for key in hashtmp.keys():
            logging.info(key)
            tmp = hash_checker(key, hashtmp, hashdict)
            tmp = array(tmp)

            try:
                outinfo = concatenate((outinfo, tmp), axis=0)
            except:
                outinfo = tmp
            logging.info()
    logging.info('processing time = %2.1f seconds' % (time.time() - start_time))
    logging.info('Done')
    return(outinfo)


if __name__ == '__main__':
    logging.info("Proceeding with duplication_checker")

    duplications, corpus = main()
    idx = where(duplications[:, 2] > 10)
    savetxt(corpus.replace('_hashes.pkl', 'duplications.txt'), duplications[idx], fmt='%s')
    logging.info("... Duplications written to {}".format(corpus.replace('_hashes.pkl', 'duplications.txt')))
