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
from collections import defaultdict

# custom packages
import pacman2020
from pacman2020 import PACManGenericText
from utils.tokenizer import PACManTokenizer


def author_query(authorlist):
    this_year = datetime.date.today().year
    r = ads.RateLimits('SearchQuery')
    ads_data = defaultdict(list)
    author_record ={}
    for author in authorlist:
        query = ads.SearchQuery(
            author=author,
            fl=['id', 'author', 'abstract', 'bibcode','title', 'citation_count','body','orcid','year'],
            q="year:{year1}-{year2}".format(year1=this_year-10, year2=this_year),
            sort='year',
            rows=300 ## hard coded to return only 300 entries per author, from the last 10 years
            )
        papers = list(query)
        author_record[author]=papers
        abstracts = []
        for paper in papers:
            abstracts.append(paper.abstract)
        abstracts = ['' if entry is None else entry for entry in abstracts]
        abstracts = [abstract.rstrip() for abstract in abstracts]
        abstracts = [abstract.strip('"') for abstract in abstracts]
        abstracts = [abstract.strip("'") for abstract in abstracts]
        abstracts = [abstract.replace('<P />','') for abstract in abstracts]
        abstracts = [
            re.sub(
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]',' ',entry
            )
            for entry in abstracts
            ]

        ### need to clean out stopwords...
        all_abstracts = ' '.join(abstracts)
        text, cleaned_text, tokens = pacman_pipeline.apply_tokenizer(all_abstracts)
        ads_data['fname'].append(author)
        ads_data['nrecords'].append(len(papers))
        ads_data['text'].append(text)
        ads_data['cleaned_text'].append(cleaned_text)
    ads_df = pd.DataFrame(ads_data)
    print (r.limits) ## use 'data -r' on reset date to get a readable datetime
    return(ads_df, author_record)


if __name__=='__main__':


    modelfile = 'strolger_pacman_model_7cycles.joblib'    
    pacman_pipeline = PACManGenericText(model_name=modelfile)
    force = False

    #authorfile = 'AAS_full_membs_for_NASA.csv'
    #authorfile = 'HST_C28_Panelists.csv'
    #authorfile = 'HST_C28_midcycle1_Panelists.csv'
    #authorfile = 'JWST_C01_Panelists.csv'
    #authorfile = 'JWST_C01_PIs.csv'
    authorfile = 'HST_C30_panelists.csv'
    
    authorpkl = authorfile.replace('.csv','.pkl')
    querypkl = authorfile.replace('.csv','_querry.pkl')
    outfile = authorfile.replace('.csv','.txt')
    foutfile2 = authorfile.replace('.csv','_matches.pkl')
    foutfile1 = authorfile.replace('.csv','_match_check.pkl')

    if ((not os.path.isfile(authorpkl)) and (not os.path.isfile(querypkl))) or force:
        author_list = pd.read_csv(authorfile,header=0)
        author_keys = [x.lower() for x in list(author_list.keys())]
        author_list.columns=author_keys
        if 'last_name' in author_keys:
            authors = [i+','+j for i, j in zip(author_list.last_name,author_list.first_name)]
        else:
            authors = author_list.name
           #authors=random.choices(authors,k=200) ## for testing a random set of 200 
        #authors=['Strolger, L.', 'Gordon, K.'] ## for coi
        ads_df, papers = author_query(authors)
        if force:
            os.remove(authorpkl)
            os.remove(querypkl)
        ads_df.to_pickle(authorpkl)
        pickle.dump(papers,open(querypkl,'wb'))
    else:
        ads_df=pd.read_pickle(authorpkl)
        papers = pickle.load(open(querypkl,'rb'))

    ### now the nitty-gritty for loading and applying model
    pacman_pipeline.load_model()
    pacman_pipeline.apply_model(ads_df, training=False)
    
    ## pacman_pipeline.model_results.info()
    if not os.path.isfile(cwd+'/model_results/production/'+outfile):
        pacman_pipeline.save_model_results(fout=outfile,training=False)
        print('Results written to %s' %outfile)
    else:
        print('%s exists, exiting without overwriting...' %outfile)
   


    ## ### for reporting on which panels.
    ## author_list = pd.read_csv(authorfile,header=0)
    ## for idx in range(len(author_list)):
    ##     print('%s, %s, %s' %(
    ##         pacman_pipeline.model_results.iloc[idx]['fname'],
    ##         pacman_pipeline.model_results.iloc[idx]['model_classification'],
    ##         author_list.iloc[idx]['Panel']
    ##         ))
            
    
    ### Testing a method to do a TF-IDF Cosine Sim
    ## def cos_sims (ads_df, cycle=28):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel


    ## this is structured wrong. Its matching proposals to reviewers.
    ## Should match reviewers to proposals
    if not os.path.isfile(foutfile1):
        best_proposals={}
        print('Working cosine similarities...\n')
        for idx in range(len(ads_df)):
            test_author = ads_df.iloc[idx].fname
            test_corpus = ads_df.iloc[idx].cleaned_text
            print('%d of %d' %(idx,len(ads_df)))
            pcorpora = []
            #for file in glob.glob('training_data/training_corpus_cy99/*_training.txt'):
            #for file in glob.glob('unclassified_proposals/corpus_cy99/*_training.txt'):
            for file in glob.glob('unclassified_proposals/corpus_cy30/*_training.txt'):
                with open(file, 'r') as paper:
                    pcorpora.append((file, paper.read()))

            tf = TfidfVectorizer(analyzer='word', ngram_range=(1,3), min_df = 0, stop_words = 'english')
            tfidf_matrix =  tf.fit_transform([test_corpus]+[content for file, content in pcorpora])
            cosine_similarities = linear_kernel(tfidf_matrix[:1], tfidf_matrix[1:]).flatten()
            ## related_docs_indices = [i for i in cosine_similarities.argsort()[::-1] if i != 0]
            related_docs_indices = cosine_similarities.argsort()[::-1]
            top_ten = [(index, cosine_similarities[index]) for index in related_docs_indices]#[0:20]
            ## print('%s' %test_author)
            ## for proposal, score in top_ten:
            ##     print('%04d, %.2f' %(
            ##         int(os.path.basename(pcorpora[proposal][0])[:4]),
            ##         score))
            ## print()
            for proposal, score in top_ten:
                try:
                    best_proposals[test_author].append([int(os.path.basename(pcorpora[proposal][0])[:5]), score])
                except:
                    best_proposals[test_author]=[[int(os.path.basename(pcorpora[proposal][0])[:5]), score]]
            best_proposals[test_author]=array(best_proposals[test_author])
        pickle.dump(best_proposals,open(foutfile1,'wb'))
    else:
        print(foutfile1,' exists... exiting.')


    ## if not os.path.isfile(foutfile2):

    ##     #for file in glob.glob('training_data/training_corpus_cy99/*_training.txt'):
    ##     for file in glob.glob('unclassified_proposals/corpus_cy99/120[12]_training.txt'):
    ##         with open(file, 'r') as paper:
    ##             test_corpus = paper.read()

    ##         pcorpora = []
    ##         for idx in range(len(ads_df)):
    ##             pcorpora.append((ads_df.iloc[idx].fname,ads_df.iloc[idx].cleaned_text))
                

    ##         tf = TfidfVectorizer(analyzer='word', ngram_range=(1,3), min_df = 0, stop_words = 'english')
    ##         tfidf_matrix =  tf.fit_transform([test_corpus]+[content for test_author, content in pcorpora])
    ##         cosine_similarities = linear_kernel(tfidf_matrix[:1], tfidf_matrix[1:]).flatten()
    ##         related_docs_indices = [i for i in cosine_similarities.argsort()[::-1] if i != 0]
    ##         top_ten = [(index, cosine_similarities[index]) for index in related_docs_indices][0:20]
    ##         ## print('%s' %test_author)
    ##         ## for proposal, score in top_ten:
    ##         ##     print('%04d, %.2f' %(
    ##         ##         int(os.path.basename(pcorpora[proposal][0])[:4]),
    ##         ##         score))
    ##         ## print()
    ##         pdb.set_trace()
    ##         for proposal, score in top_ten:
    ##             try:
    ##                 best_proposals[test_author].append([int(os.path.basename(pcorpora[proposal][0])[:4]), score])
    ##             except:
    ##                 best_proposals[test_author]=[[int(os.path.basename(pcorpora[proposal][0])[:4]), score]]
    ##         best_proposals[test_author]=array(best_proposals[test_author])
    ##     pickle.dump(best_proposals,open(foutfile2,'wb'))
    ## else:
    ##     print(foutfile2,' exists... exiting.')

   ##  pdb.set_trace()

    
