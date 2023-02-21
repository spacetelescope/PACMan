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
from sklearn.metrics import confusion_matrix, plot_confusion_matrix
from sklearn.metrics import classification_report, make_scorer, accuracy_score
from sklearn.model_selection import cross_val_score, train_test_split, cross_val_predict

# custom packages that are all in the github repo
import pacman2020
from pacman2020 import PACManTrain, PACManPipeline
from utils.proposal_scraper import HSTProposalScraper
from utils.analyzer import PACManAnalyze

def combine_proposals(pmdf):
    mykeys = ['cycle_28','cycle_27','cycle_26','cycle_25','cycle_24','cycle_23','cycle_22']
    for key in pmdf.proposal_data.keys():
    ## for key in mykeys:
        tmpdf = pmdf.proposal_data[key]
        try:
            outdf=outdf.append(tmpdf, sort=True)
        except:
            outdf = tmpdf
    return outdf

def classification_report_with_accuracy_score(y_true, y_pred):
    print(classification_report(y_true, y_pred)) # print classification report
    return accuracy_score(y_true, y_pred) # return accuracy score

def get_balanced_subset(df, proposal_counts):
    min_num_proposals = proposal_counts.min()
    data = {}
    for proposal_type in df['hand_classification'].unique():
        proposal_df = df[df['hand_classification'] == proposal_type]
        indices = np.random.randint(low=0, high=len(proposal_df), size=100)
        data[proposal_type] = proposal_df.iloc[indices]
    
    final_df = pd.DataFrame()
    for key in data.keys():
        final_df = final_df.append(data[key])
    return final_df

if __name__=='__main__':

    ## load stored corpora
    loadmodel = True
    loadfile = True

    cval = 7
    savefile = cwd+'/store/saved_corpora_7cycles.pkl'
    modelfile = 'strolger_pacman_model_7cycles.joblib'

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
            pacman_scraper = HSTProposalScraper(for_training=True, cycles_to_analyze=[22, 23, 24, 25, 26, 27, 28])
            pacman_scraper.scrape_cycles()

            # Now lets stoire a training set...
            pacman_training = PACManTrain(cycles_to_analyze=[22, 23, 24, 25, 26, 27, 28])
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


    pacman_testing = pickle.load(open(savefile,'rb'))
    total_dataset = combine_proposals(pacman_testing)
    ## total_dataset = pacman_testing.proposal_data['cycle_27']
        
    total_proposal_counts = total_dataset['hand_classification'].value_counts()
    balanced_df = get_balanced_subset(df=total_dataset, proposal_counts=total_proposal_counts)

    training_pacman = PACManPipeline(model_name=modelfile)
    training_pacman.load_model()
    
    crossvalscoreraw=False
    if crossvalscoreraw:
        scorestotal = cross_val_score(
            training_pacman.model, 
            total_dataset['cleaned_text'], 
            total_dataset['encoded_hand_classification'], 
            cv=cval, 
            scoring=make_scorer(classification_report_with_accuracy_score)
            )
        print('%2.1f+/-%2.1f'%(average(scorestotal)*100.,std(scorestotal)*100.))

    crossvalscorebal=False
    if crossvalscorebal:
        scoresbalanced = cross_val_score(
            training_pacman.model, 
            balanced_df['cleaned_text'], 
            balanced_df['encoded_hand_classification'], 
            cv=cval, 
            scoring='f1_macro'
            )
        print('%2.1f+/-%2.1f'%(average(scoresbalanced)*100.,std(scoresbalanced)*100.))


    scoresbalanced = cross_val_score(training_pacman.model, balanced_df['cleaned_text'], balanced_df['encoded_hand_classification'], cv=cval, scoring='precision_macro')
    print('%2.1f+/-%2.1f'%(average(scoresbalanced)*100.,std(scoresbalanced)*100.))

    confmatrix=False
    if confmatrix:
        ## confusion matrix
        ## y_pred=cross_val_predict(training_pacman.model, balanced_df['cleaned_text'], balanced_df['encoded_hand_classification'], cv=cval)

        ## conf_mat = confusion_matrix(balanced_df['encoded_hand_classification'],y_pred)

        class_names = ['Exopl.','Gal.','IGM', 'LSS','Sol.', 'Stars','StPops','AGN']
        titles_options = [("Confusion matrix, without normalization", None, '3d'),
                          ("Normalized confusion matrix", 'true','0.2f')]
        cnt=0
        for title, normalize, my_format in titles_options:
            cnt+=1
            disp = plot_confusion_matrix(training_pacman.model,  total_dataset['cleaned_text'],
                                         total_dataset['encoded_hand_classification'],
                                         display_labels=class_names,
                                         values_format=my_format,
                                         cmap=plt.cm.Blues,
                                         xticks_rotation=45,
                                         normalize=normalize)
            grid(False)
            disp.ax_.set_title(title)
            print(title)
            print(disp.confusion_matrix)
            savefig('conf_mat_%1d.png'%cnt)


    ## now to do top two categories
    training_pacman.apply_model(df=total_dataset,training=True)
    pacman_analyzing = PACManAnalyze()
    pacman_analyzing.encoder = training_pacman.encoder
    pacman_analyzing.compute_accuracy_measurements(df=training_pacman.model_results, normalize=True)
    print(f"computed accuracy: {pacman_analyzing.computed_accuracy['top'].sum()/pacman_analyzing.computed_accuracy.sum().sum():.0%}")
    print(f"computed accuracy: {pacman_analyzing.computed_accuracy['top_two'].sum()/pacman_analyzing.computed_accuracy.sum().sum():.0%}")
    pacman_analyzing.plot_barh_all(100*pacman_analyzing.computed_accuracy.loc[:,['top','top_two','misclassified']], fout='test.png')
    pdb.set_trace()


