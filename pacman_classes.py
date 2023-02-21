#!/usr/bin/env python
"""
The :py:mod:`~pacman_classes` module contains two classes,
:py:class:`~pacman_classes.PACManPipeline` and :py:class:`~pacman_classes.PACManTrain`,
which are designed to facilitate the process of text pre-processing, training,
testing, and applying the model to unclassified proposals.
"""

from collections import defaultdict
import glob
import logging
import os
import time
import string

import dask
from dask.diagnostics import ProgressBar
import joblib
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline

import tqdm
from utils.tokenizer import PACManTokenizer

from scripts import constants as constants
config = constants.config
#configfile = "./config.json"
#with open(configfile) as data_file:
#    config = json.loads(data_file.read())


class PACManPipeline(PACManTokenizer):
    """ This class provides functionality for classifying new proposals.

    Parameters
    ----------
    cycle : int
        The HST Cycle number to analyze
    model_name : str
        The name of one of the trained models in the ~/PACman_dist/models
        directory.
    """
    def __init__(self, cycle=None, model_name=''):

        super().__init__()
        self._base = os.path.join(
            '/',
            *os.path.dirname(os.path.abspath(__file__)).split('/')
        )
        self._unclassified_dir = os.path.join(self.base,
                                            constants.path_proposals_processed)
                            #config['training_filepath'].split('/')[0]
        self._model_name = config['models_dir'] + model_name
        self._results_dir = constants.path_model_results #config['results_dir'][:-1]
        self._cycle = cycle
        self._proposal_data = {}
        self._encoder = LabelEncoder()
        self._model = None

    @property
    def base(self):
        """Base path of the PACMan package"""
        return self._base

    @base.setter
    def base(self, value):
        self._base = value

    @property
    def cycle(self):
        """Proposal cycle we are analyzing"""
        return self._cycle

    @cycle.setter
    def cycle(self, value):
        self._cycle = value

    @property
    def encoder(self):
        """Encoder used by the classifier"""
        return self._encoder

    @encoder.setter
    def encoder(self, value):
        self._encoder = value

    @property
    def model(self):
        """Pre-trained classifier"""
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def model_name(self):
        """Absolute path of the pre-trained model"""
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        self._model_name = value

    @property
    def results_dir(self):
        """Directory where results from the model are stored"""
        return self._results_dir

    @results_dir.setter
    def results_dir(self, value):
        self._results_dir = value

    @property
    def proposal_data(self):
        """`py:class:dict` for storing the DataFrame of proposal data"""
        return self._proposal_data

    @proposal_data.setter
    def proposal_data(self, value):
        self._proposal_data = value

    @property
    def unclassified_dir(self):
        """Directory containing unclassified proposals"""
        return self._unclassified_dir

    @unclassified_dir.setter
    def unclassified_dir(self, value):
        self._unclassified_dir = value

    def apply_model(self, df, training=False):
        """ Apply the model to make predictions on input data

        Parameters
        ----------
        df

        Returns
        -------

        """
        try:
            X = df['cleaned_text']
        except KeyError:
            #print("""Please check that all input files are in the correct directories.
            #You may need to run categorize_one_cycle once with each cycle listed as main_test_cycle in config.json""")
            raise ValueError("Please check that all input files are in the "
                            +"correct directories. You may need to run "
                            +"categorize_one_cycle once with each cycle listed "
                            +"as main_test_cycle in config.json.")
        self.predictions = self.model.predict(X)
        self.predicition_probabilities = self.model.predict_proba(X)
        if training:
            self.model_results = df.loc[
                                 :,
                                 ['fname',
                                  'hand_classification',
                                  'encoded_hand_classification']
                                 ]
        else:
            self.model_results = df.loc[:, ['fname']]
        # Add the encoded model classifications to the DataFrame
        self.model_results['encoded_model_classification'] = self.predictions

        # Add the decoded model classifications
        self.model_results['model_classification'] = \
            self.encoder.inverse_transform(self.predictions)

        # Now we need to add the probabilities for each class
        for i, classname in enumerate(self.encoder.classes_):
            colname = f"{self.encoder.classes_[i].replace(' ', '_')}_prob"
            self.model_results[colname] = self.predicition_probabilities[:, i]

    def save_model_results(self, fout=None, training=False):
        """ Save the classification results to file

        Parameters
        ----------
        fout : str
            Filename for output file. Defaults to the name of model and the
            proposal cycle number.
        training : bool
            If True, then the results are saved in the training sub directory.
            If False, then the results are saved in the production sub
            directory.

        Returns
        -------

        """
        if fout is None:
            fout = f"{self.model_name.split('.')[0]}_results_{self.cycle}.txt"

        if training:
            fout = os.path.join(
                self.results_dir,
                'training',
                fout
            )
        else:
            fout = os.path.join(
                self.results_dir,
                fout
            )
        self.model_results.to_csv(fout, header=True, index=False)

    def load_model(self, model_name=None):
        """ Load the production model for PACman

        Parameters
        ----------
        model_file

        Returns
        -------

        """

        if model_name is not None:
            self.model_name = model_name
        logging.info(f"Loading model stored at \n {self.model_name}")
        self.model = joblib.load(self.model_name)

        logging.info(f"Loading encoder information...")
        classes = np.load(
            self.model_name.replace('.joblib', '_encoder_classes.npy'),
            allow_pickle=True
        )
        self.encoder.classes_ = classes

    def preprocess(self, flist, parallel=True):
        """ Perform the necessary pre-processing steps

        Parameters
        ----------
        flist : list
            Description
        """

        if self.stop_words is None:
            self.get_stop_words(fname=self.stop_words_file)

        st = time.time()
        data = defaultdict(list)
        if parallel:
            delayed_obj = [
                dask.delayed(self.run_tokenization)(fname=f, plot=False)
                for f in tqdm.tqdm(flist,ascii=True)
            ]
            with ProgressBar():
                results = dask.compute(
                    *delayed_obj,
                    scheduler='threads',
                    num_workers=4
                )
        else:
            results = [
                self.run_tokenization(fname=f, plot=False)
                for f in tqdm.tqdm(flist)
            ]

        for i, (text, cleaned_text, tokens) in enumerate(results):
            data['text'].append(text)
            data['cleaned_text'].append(cleaned_text)
            data['fname'].append(flist[i])
            # Parse the proposal number from the file name
            # TODO: Find a better way to extract numbers out of the filename
            try:
                proposal_num = int(
                    flist[i].split('/')[-1].split('_')[0]
                )
            except ValueError:
                proposal_num = int(
                    flist[i].split('/')[-1].split('_')[0].split('.')[0]
                )
            data['proposal_num'].append(proposal_num)
        df = pd.DataFrame(data)
        et = time.time()
        duration = (et - st)/60
        logging.info(f"Total time for preprocessing: {duration:.3f}")
        return df

    def read_unclassified_data(self, cycle=None, parallel=True, N=None):
        """ Read in the data for the specified cycle and perform preprocessing

        Parameters
        ----------
        cycle
        parallel

        Returns
        -------

        """
        if cycle is not None:
            self.cycle = cycle
        path_to_data = os.path.join(
            self.unclassified_dir,
            self.cycle
        )

        #flist = glob.glob(path_to_data+config['training_suffix'])
        flist = glob.glob(path_to_data+constants.training_suffix)

        if N is None:
            N = len(flist)

        logging.info(
            (f"Reading in {N} proposals...\n"
             f"Data Directory: {path_to_data}")
        )

        df = self.preprocess(flist=flist[:N], parallel=parallel)
        self.proposal_data[self.cycle] = df


class PACManTrain(PACManPipeline):
    """ This class provides the functionality required for training a model

    The core functionality is as follows,

        * Read in multiple cycles worth of proposals and perform the
        necessary pre-processing steps for text data

        * Generate an encoding for mapping category names to integer
        labels

        * Create a scikit-learn Pipeline object for vectorizing training
        data and feeding it into a multi-class classification model

        * Write the trained model and encoder out file

    Parameters
    ----------
    cycles_to_analyze : list
        A list of strings mapping to proposal cycles. Each proposal in the
        list will be processed.

    """
    def __init__(self, cycles_to_analyze=['Cycle24', 'Cycle25']):

        PACManPipeline.__init__(self)
        self.training_dir = config['training_filepath']
        ## self.training_dir = os.path.join(
        ##     self.base,
        ##     'unclassified_proposals'
        ## )
        self.cycles_to_analyze = cycles_to_analyze
        self.proposal_data = {}
        self.encoders = {}

    def read_training_data(self, parallel=True):
        """ Read in training data

        For each cycle, read in and pre-process the proposals training corpora.
        Note that in order for data to be used for training, it must have a
        cycle_N_hand_classifications.txt file located in the output directory.

        Returns
        -------
        """

        # First, read in our custom list of stop words using the
        # get_stop_words() method of the PACManTokenizer object

        for cycle in self.cycles_to_analyze:
            path_to_data = os.path.join(
                self.training_dir,
                'training_corpus_%s'%(cycle)
            )

            flist = glob.glob(
                f"{path_to_data}/*training.txt")
            N = len(flist)

            logging.info(
                (f"Reading in {N} proposals...\n"
                 f"Data Directory: {path_to_data}")
            )

            df = self.preprocess(flist=flist, parallel=parallel)

            hand_classifications = pd.read_csv(
                config["output_dir"]+cycle+config["compare_results_by_hand_file"]
            )
            try:
                merged_df = pd.merge(df, hand_classifications, on='proposal_num')
            except:
                import pdb; pdb.set_trace()
            self.proposal_data[cycle] = merged_df
            labels = self.encoder.fit_transform(
                self.proposal_data[cycle]['hand_classification']
                )
            self.proposal_data[cycle]['encoded_hand_classification']\
                = labels

    def fit_model(self, df, clf=None, vect=None, sample_weight=1):
        """ Make a Pipeline object and use it to fit the dataset

        If no classifier or vectorizer is passed, then the defaults are used:
            - clf --> MultinomialNB(alpha=0.05)
            - vect --> TfidfVectorizer(
                            max_features=10000,
                            use_idf=True,
                            norm='l2',
                            ngram_range=(1, 2)
                        )

        Parameters
        ----------
        df : pd.DataFrame
            Pandas DataFrame containing the training data

        clf : classifier
            Multi-class classifier from scikit-learn

        vect : vectorizer
            Vectorizer to use for generating the lexicon

        Returns
        -------

        """
        if clf is None:
            #clf = ComplementNB()#(alpha=0.05)
            clf = MultinomialNB(alpha=0.05)
        if vect is None:
            vect = TfidfVectorizer(
                max_features=10000,
                use_idf=True,
                norm='l2',
                ngram_range=(1, 2)
            )

        self.model = Pipeline(
            [('vect', vect),
             ('clf', clf)]
        )
        self.model.fit(df['cleaned_text'], df['encoded_hand_classification'])

    def save_model(self, fname=None):
        """ Write the model to file, must have .joblib extension

        Parameters
        ----------
        fname

        Returns
        -------

        """
        logging.info('Saving model and encoder information...')
        if fname is not None:
            fout = fname
            fout_encoder = fname.replace('.joblib', '_encoder_classes.npy')
        else:
            fout = 'pacman_model.joblib'
            fout_encoder = fout.replace('.joblib', '_encoder_classes.npy')

        fout = os.path.join(
            # self.base,
            # 'models',
            fout
        )
        fout_encoder = os.path.join(
            # self.base,
            # 'models',
            fout_encoder
        )
        np.save(fout_encoder, self.encoder.classes_)
        joblib.dump(self.model, fout)


class PACManGenericText(PACManTokenizer):

    def __init__(self, model_name=''):

        super().__init__()
        self._base = os.path.join(
            '/',
            *os.path.dirname(os.path.abspath(__file__)).split('/')
        )
        self._model_name = os.path.join(
            self.base,
            'models',
            model_name
        )
        self._results_dir = os.path.join(
            self.base,
            'model_results'
        )
        self._proposal_data = {}
        self._encoder = LabelEncoder()
        self._model = None

    @property
    def base(self):
        """Base path of the PACMan package"""
        return self._base

    @base.setter
    def base(self, value):
        self._base = value

    @property
    def encoder(self):
        """Encoder used by the classifier"""
        return self._encoder

    @encoder.setter
    def encoder(self, value):
        self._encoder = value

    @property
    def model(self):
        """Pre-trained classifier"""
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def model_name(self):
        """Absolute path of the pre-trained model"""
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        self._model_name = value

    @property
    def results_dir(self):
        """Directory where results from the model are stored"""
        return self._results_dir

    @results_dir.setter
    def results_dir(self, value):
        self._results_dir = value

    @property
    def proposal_data(self):
        """`py:class:dict` for storing the DataFrame of proposal data"""
        return self._proposal_data

    @proposal_data.setter
    def proposal_data(self, value):
        self._proposal_data = value

    def apply_model(self, df, training=False):
        """ Apply the model to make predictions on input data

        Parameters
        ----------
        df

        Returns
        -------

        """
        X = df['cleaned_text']
        self.predictions = self.model.predict(X)
        self.predicition_probabilities = self.model.predict_proba(X)
        if training:
            self.model_results = df.loc[:, ['fname',
                                            'hand_classification',
                                            'encoded_hand_classification']
                                        ]
        else:
            self.model_results = df.loc[:, ['fname']]

        # Add the encoded model classifications to the DataFrame
        self.model_results['encoded_model_classification'] = self.predictions

        # Add the decoded model classifications
        self.model_results['model_classification'] = \
            self.encoder.inverse_transform(self.predictions)

        # Now we need to add the probabilities for each class
        for i, classname in enumerate(self.encoder.classes_):
            colname = f"{self.encoder.classes_[i].replace(' ', '_')}_prob"
            self.model_results[colname] = self.predicition_probabilities[:, i]

    def save_model_results(self, fout=None, training=False):
        """ Save the classification results to file

        Parameters
        ----------
        fout : str
            Filename for output file. Defaults to the name of model and the
            proposal cycle number.
        training : bool
            If True, then the results are saved in the training sub directory.
            If False, then the results are saved in the production sub
            directory.

        Returns
        -------

        """
        if fout is None:
            fout = f"{self.model_name.split('.')[0]}_results_{self.cycle}.txt"

        if training:
            fout = os.path.join(
                # self.results_dir,
                'training',
                fout
            )
        else:
            fout = os.path.join(
                # self.results_dir,
                # 'production',
                fout
            )
        self.model_results.to_csv(fout, header=True, index=False)

    def load_model(self, model_name=None):
        """ Load the production model for PACman

        Parameters
        ----------
        model_file

        Returns
        -------

        """

        if model_name is not None:
            self.model_name = model_name
        logging.info(f"Loading model stored at \n {self.model_name}")
        self.model = joblib.load(self.model_name)

        logging.info(f"Loading encoder information...")
        classes = np.load(
            self.model_name.replace('.joblib', '_encoder_classes.npy'),
            allow_pickle=True
        )
        self.encoder.classes_ = classes

    def apply_tokenizer(self, text):
        if self.stop_words is None:
            self.get_stop_words(fname=self.stop_words_file)

        tokens = self.spacy_tokenizer(
            text,
            stop_words=self.stop_words,
            punctuations=string.punctuation
            )
        cleaned_text = ' '.join(tokens)
        return text, cleaned_text, tokens
