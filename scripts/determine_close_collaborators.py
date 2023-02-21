#!/usr/bin/env python
import os
import pickle
import json
import datetime
import pandas as pd
from collections import Counter
import logging
from scripts.categorize_ads_reviewers import author_query

from scripts import constants as constants
config = constants.config

#configfile = "./config.json"
#with open(configfile) as data_file:
#    config = json.loads(data_file.read())

collaborator_time_frame = config['close_collaborator_time_frame']


def anyCollaborators(papers):
    '''
    Find any author in the last collaborator_time_frame-years (default 3)
    create a list of collaborators in refereed papers
    '''
    logging.info("Determining collaborators who published with the author")
    this_year = datetime.date.today().year
    collaborators = {}
    for author in papers.keys():
        tmp = []
        for paper in papers[author]:
            if ((this_year - int(paper.year)) <= collaborator_time_frame):
                tmp += paper.author
        newlist = []
        for item in tmp:
            try:
                newlist.append(item.split(',')[0]+', '+item.split(',')[1][1]+'.')
            except:
                newlist.append(item)
        collaborators[author] = sorted(set(newlist))
    return(collaborators)


def frequentCollaborators(papers, pis=None):
    '''
    any author in the last collaborator_time_frame-years
    published 3 or more times together
    create a list of collaborators in refereed papers
    '''
    logging.info("Determining collaborators who published three or more times together")
    this_year = datetime.date.today().year
    collaborators = {}
    for author in papers.keys():
        tmp = []
        for paper in papers[author]:
            if ((this_year - int(paper.year)) <= collaborator_time_frame):
                if pis:
                    tmp += paper.author[:pis]
                else:
                    tmp += paper.author
        newlist = []
        for item in tmp:
            try:
                newlist.append(item.split(',')[0]+', '+item.split(',')[1][1]+'.')
            except:
                newlist.append(item)
        counts = Counter(newlist)
        hicounts = Counter({k: c for k, c in counts.items() if c >= 3})
        collaborators[author] = {k: c for k, c in hicounts.items()}
    return(collaborators)


def main():
    force = False

    authorfile_inp = os.path.join(constants.input_panelist_dir,
                    (config['main_test_cycle']+constants.authorfile_suffix))
    authorfile_out = os.path.join(constants.path_output,
                    (config['main_test_cycle']+constants.authorfile_suffix))
    authorpkl = authorfile_out.replace('.csv', '.pkl')
    querypkl = authorfile_out.replace('.csv', '_query.pkl')
    outfile = authorfile_out.replace('.csv', '_conflicts.pkl')

    logging.info("Using author file" + authorfile_inp)

    if not os.path.isfile(querypkl) or force:
        author_list = pd.read_csv(authorfile_inp, header=0)
        author_keys = [x.lower() for x in list(author_list.keys())]
        author_list.columns = author_keys
        if 'last_name' in author_keys:
            authors = [i+','+j for i, j in zip(author_list.last_name, author_list.first_name)]
        else:
            authors = author_list.name
            # authors=random.choices(authors,k=200) ## for testing a random set of 200
            # authors=['Strolger, L.', 'Gordon, K.'] ## for coi
        ads_df, papers = author_query(authors)
        if force:
            os.remove(authorpkl)
            os.remove(querypkl)
        ads_df.to_pickle(authorpkl)
        with open(querypkl, 'wb') as openfile:
            pickle.dump(papers, openfile)
    else:
        with open(authorpkl, 'rb') as openfile:
            ads_df = pickle.load(openfile)
        with open(querypkl, 'rb') as openfile:
            papers = pickle.load(openfile)

    if not os.path.isfile(outfile) or force:
        collaborator_dict = frequentCollaborators(papers, pis=3)
        with open(outfile, 'wb') as openfile:
            pickle.dump(collaborator_dict, openfile)
    else:
        logging.info(outfile + ' already exists... exiting')


if __name__ == '__main__':
    logging.info("Proceeding with determine_close_collaborators")
    main()
    print("wow_0")
    print(os.listdir(constants.input_panelist_dir))
