#!/usr/bin/env python
import os
import pickle
import json
from pylab import *
import logging

# open source packages
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay, plot_confusion_matrix
from sklearn.metrics import classification_report, make_scorer, accuracy_score
from sklearn.model_selection import cross_val_score

# custom packages that are all in the github repo
from pacman_classes import PACManTrain, PACManPipeline
from utils.proposal_scraper import ProposalScraper
from utils.analyzer import PACManAnalyze
from scripts import constants as constants
config = constants.config


def combine_proposals(pmdf):
    for key in pmdf.proposal_data.keys():
        tmpdf = pmdf.proposal_data[key]
        try:
            outdf = outdf.append(tmpdf, sort=True)
        except:
            outdf = tmpdf
    return outdf


def classification_report_with_accuracy_score(y_true, y_pred):
    logging.info(classification_report(y_true, y_pred))
    return accuracy_score(y_true, y_pred)


def get_balanced_subset(df):
    data = {}
    for proposal_type in df['hand_classification'].unique():
        proposal_df = df[df['hand_classification'] == proposal_type]
        indices = np.random.randint(low=0, high=len(proposal_df), size=100)
        data[proposal_type] = proposal_df.iloc[indices]

    final_df = pd.DataFrame()
    for key in data.keys():
        final_df = final_df.append(data[key])
    return final_df


def main():
    #configfile = "./config.json"
    #with open(configfile) as data_file:
    #    config = json.loads(data_file.read())

    # load stored corpora
    #if config['load_model'] == "true":
    #    loadmodel = True
    #else:
    #    loadmodel = False
    #if config['load_file'] == "true":
    #    loadfile = True
    #else:
    #    loadfile = False
    loadmodel = constants.load_model
    loadfile = constants.load_file

    cval = 7
    savefile = os.path.join(constants.path_output,
                            constants.cross_validate_savefile)
    modelfile = config['modelfile']
    path_modelfile = os.path.join(config['models_dir'], modelfile)

    if not loadmodel or not os.path.isfile(path_modelfile):
        if os.path.isfile(savefile) and loadfile:
            logging.info('-'*58)
            logging.info('Loading %s' % savefile)
            with open(savefile, 'rb') as openfile:
                pacman_training = pickle.load(openfile)

        else:
            logging.info('-'*58)
            logging.info('Creating %s' % savefile)

            if os.path.isfile(savefile):
                os.remove(savefile)
            # Make an instance of the proposal scraping and scrape each cycle
            pacman_scraper = ProposalScraper(for_training=True, cycles_to_analyze=config['past_cycles'])
            pacman_scraper.scrape_cycles()

            # Now lets store a training set...
            pacman_training = PACManTrain(cycles_to_analyze=config['past_cycles'])
            pacman_training.read_training_data(parallel=False)
            with open(savefile, 'wb') as openfile:
                pickle.dump(pacman_training, openfile)

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
        if os.path.isfile(path_modelfile):
            logging.info('removing %s' % modelfile)
            os.remove(path_modelfile)
        logging.info('saving %s' % modelfile)
        pacman_training.save_model(fname=path_modelfile)

    with open(savefile, 'rb') as openfile:
        pacman_testing = pickle.load(openfile)  # error looking for pacman2020
    total_dataset = combine_proposals(pacman_testing)
    # total_dataset = pacman_testing.proposal_data['cycle_27']

    total_proposal_counts = total_dataset['hand_classification'].value_counts()
    balanced_df = get_balanced_subset(df=total_dataset)

    training_pacman = PACManPipeline(model_name=modelfile)
    training_pacman.load_model()

    if config['cross_val_score_raw'] == "true":
        scorestotal = cross_val_score(
            training_pacman.model,
            total_dataset['cleaned_text'],
            total_dataset['encoded_hand_classification'],
            cv=cval,
            n_jobs=-1,
            scoring=make_scorer(classification_report_with_accuracy_score)
            )
        logging.info('Accuracy: %2.1f+/-%2.1f' % (average(scorestotal)*100., std(scorestotal)*100.))

    if config['cross_val_score_bal'] == "true":
        scoresbalanced = cross_val_score(
            training_pacman.model,
            balanced_df['cleaned_text'],
            balanced_df['encoded_hand_classification'],
            cv=cval,
            n_jobs=-1,
            scoring='f1_macro'
            )
        logging.info('f1: %2.1f+/-%2.1f' % (average(scoresbalanced)*100., std(scoresbalanced)*100.))

    scoresbalanced = cross_val_score(training_pacman.model, balanced_df['cleaned_text'], balanced_df['encoded_hand_classification'], cv=cval, scoring='precision_macro')
    logging.info('Precision: %2.1f+/-%2.1f' % (average(scoresbalanced)*100., std(scoresbalanced)*100.))

    #if config['conf_matrix'] == "true":
    if constants.conf_matrix:
        logging.info("Determining confusion matrix")
        # confusion matrix
        # y_pred=cross_val_predict(training_pacman.model, balanced_df['cleaned_text'], balanced_df['encoded_hand_classification'], cv=cval)

        # conf_mat = confusion_matrix(balanced_df['encoded_hand_classification'],y_pred)

        class_names = constants.class_names
        titles_options = [("Confusion matrix, without normalization", None, '3d'),
                          ("Normalized confusion matrix", 'true', '0.2f')]
        cnt = 0
        for title, normalize, my_format in titles_options:
            cnt += 1
            disp = plot_confusion_matrix(training_pacman.model,  total_dataset['cleaned_text'],
                                         total_dataset['encoded_hand_classification'],
                                         display_labels=class_names,
                                         values_format=my_format,
                                         cmap=plt.cm.Blues,
                                         xticks_rotation=45,
                                         normalize=normalize)
            grid(False)
            disp.ax_.set_title(title)
            disp.ax_.set_ylabel('Manual Classification')
            logging.info(title)
            logging.info(disp.confusion_matrix)
            savefig('conf_mat_%1d.pdf' % cnt)

    # now to do top two categories
    training_pacman.apply_model(df=total_dataset, training=True)
    pacman_analyzing = PACManAnalyze()
    pacman_analyzing.encoder = training_pacman.encoder
    pacman_analyzing.compute_accuracy_measurements(df=training_pacman.model_results, normalize=True)
    pacman_analyzing.computed_accuracy['class_names'] = class_names
    logging.info(f"computed accuracy (top category): {pacman_analyzing.computed_accuracy['top'].sum()/pacman_analyzing.computed_accuracy.iloc[:,:-1].sum().sum():.1%}")
    logging.info(f"computed accuracy (top 2 categories): {pacman_analyzing.computed_accuracy['top_two'].sum()/pacman_analyzing.computed_accuracy.iloc[:,:-1].sum().sum():.1%}")
    pacman_analyzing.plot_barh_all(100*pacman_analyzing.computed_accuracy.set_index('class_names').loc[:, ['top', 'top_two', 'misclassified']], fout='figure_bar_plot.pdf')

    logging.info("Completed cross-validation")


if __name__ == ' __main__':
    main()
