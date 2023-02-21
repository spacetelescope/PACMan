#!/usr/bin/env python
import os
import sys
import glob
import pickle
import json
from pylab import *
import datetime
import logging

# open source packages
# import ads.sandbox as ads
import ads
import pandas as pd
import re
from collections import defaultdict

# custom packages
from pacman_classes import PACManGenericText
from scripts import constants as constants

#configfile = "./config.json"
#with open(configfile) as data_file:
#    config = json.loads(data_file.read())
config = constants.config

modelfile = config['modelfile']
pacman_pipeline = PACManGenericText(model_name=modelfile)


def author_query(authorlist):
    this_year = datetime.date.today().year
    r = ads.RateLimits('SearchQuery')
    ## logging.info("current limits for ADS use:", r.limits)  # use 'data -r' on reset date to get a readable datetime
    ads_data = defaultdict(list)
    author_record = {}
    for author in authorlist:
        query = ads.SearchQuery(
            author=author,
            fl=['id', 'author', 'abstract', 'bibcode', 'title', 'citation_count', 'body', 'orcid', 'year'],  # field list
            q="year:{year1}-{year2}".format(year1=this_year-10, year2=this_year),
            sort='year',
            rows=300  # hard coded to return only 300 entries per author, from the last 10 years
            )

        # GETTING UNAUTHORIZED API RESPONSE ERROR
        # query2 = ads.SearchQuery(author=author, fl=['id', 'author', 'title', 'year'], q="year:{year1}-{year2}".format(year1=this_year-10, year2=this_year), sort='year', rows=30)
        # import pdb
        # pdb.set_trace()

        papers = list(query)
        author_record[author] = papers
        abstracts = []
        for paper in papers:
            abstracts.append(paper.abstract)
        abstracts = ['' if entry is None else entry for entry in abstracts]
        abstracts = [abstract.rstrip() for abstract in abstracts]
        abstracts = [abstract.strip('"') for abstract in abstracts]
        abstracts = [abstract.strip("'") for abstract in abstracts]
        abstracts = [abstract.replace('<P />', '') for abstract in abstracts]
        abstracts = [
            re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', ' ', entry)
            for entry in abstracts
            ]

        # need to clean out stopwords...
        all_abstracts = ' '.join(abstracts)
        text, cleaned_text, tokens = pacman_pipeline.apply_tokenizer(all_abstracts)
        ads_data['fname'].append(author)
        ads_data['nrecords'].append(len(papers))
        ads_data['text'].append(text)
        ads_data['cleaned_text'].append(cleaned_text)
    ads_df = pd.DataFrame(ads_data)
    return(ads_df, author_record)


def main():
    force = False

    authorfile_inp = os.path.join(
                        constants.input_panelist_dir,#constants.path_output,
                        config['main_test_cycle']+constants.authorfile_suffix)
    authorfile_out = os.path.join(constants.path_output,
                        config['main_test_cycle']+constants.authorfile_suffix)

    authorpkl = authorfile_out.replace('.csv', '.pkl')
    querypkl = authorfile_out.replace('.csv', '_query.pkl')
    outfile = authorfile_out.replace('.csv', '.txt')
    foutfile1 = authorfile_out.replace('.csv', '_match_check.pkl')

    if ((not os.path.isfile(authorpkl)) and (not os.path.isfile(querypkl))) or force:
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
        pickle.dump(papers, open(querypkl, 'wb'))
    else:
        ads_df = pd.read_pickle(authorpkl)
        papers = pickle.load(open(querypkl, 'rb'))

    # now the nitty-gritty for loading and applying model
    pacman_pipeline.load_model()
    pacman_pipeline.apply_model(ads_df, training=False)

    # pacman_pipeline.model_results.info()
    #if not os.path.isfile(config['results_dir']+outfile.split('/')[-1]):
    if not os.path.isfile(os.path.join(constants.path_model_results,
                                    outfile.split('/')[-1])):
        pacman_pipeline.save_model_results(fout=outfile, training=False)
        logging.info('Results written to %s' % outfile)
    else:
        logging.info('%s exists, exiting without overwriting...' % outfile)

    # Testing a method to do a TF-IDF Cosine Sim
    # def cos_sims (ads_df, cycle=28):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    # this is structured wrong. Its matching proposals to reviewers.
    # Should match reviewers to proposals
    if not os.path.isfile(foutfile1):
        best_proposals = {}
        logging.info('Working cosine similarities...\n')
        for idx in range(len(ads_df)):
            test_author = ads_df.iloc[idx].fname
            test_corpus = ads_df.iloc[idx].cleaned_text
            logging.info('%d of %d' % (idx, len(ads_df)))
            pcorpora = []
            for file in glob.glob(os.path.join(constants.path_proposals_processed,
                                                (config["main_test_cycle"]
                                                +constants.training_suffix))):
                with open(file, 'r') as paper:
                    pcorpora.append((file, paper.read()))

            tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), min_df=0, stop_words='english')
            tfidf_matrix = tf.fit_transform([test_corpus]+[content for file, content in pcorpora])
            cosine_similarities = linear_kernel(tfidf_matrix[:1], tfidf_matrix[1:]).flatten()
            related_docs_indices = cosine_similarities.argsort()[::-1]
            top_ten = [(index, cosine_similarities[index]) for index in related_docs_indices]
            for proposal, score in top_ten:
                try:
                    best_proposals[test_author].append([int(os.path.basename(pcorpora[proposal][0])[:5]), score])
                except:
                    best_proposals[test_author] = [[int(os.path.basename(pcorpora[proposal][0])[:5]), score]]
            best_proposals[test_author] = array(best_proposals[test_author])
        pickle.dump(best_proposals, open(foutfile1, 'wb'))
    else:
        logging.info(foutfile1, ' exists... exiting.')


if __name__ == '__main__':
    logging.info("Proceeding with categorize_ads_reviewers")
    main()
