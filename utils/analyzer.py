#!/usr/bin/env python

import os

from matplotlib.ticker import AutoMinorLocator
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pandas as pd


class PACManAnalyze():
    def __init__(self):
        """ This class provides functionality for analyzing the model results
        """
        self._cycle = None
        self._computed_accuracy = None
        self._model_results = None

    @property
    def model_results(self):
        """PACMan classification results"""
        return self._model_results

    @model_results.setter
    def model_results(self, value):
        self._model_results = value

    @property
    def computed_accuracy(self):
        """Computed accuracy of the classifier"""
        return self._computed_accuracy

    @computed_accuracy.setter
    def computed_accuracy(self, value):
        self._computed_accuracy = value

    def load_model_results(self, fname=None, training=False):
        if training:
            fname = os.path.join(
                self.results_dir,
                'training',
                fname
            )
        else:
            fname = os.path.join(
                self.results_dir,
                'production',
                fname
            )
        return pd.read_csv(fname, header=0)

    def compute_accuracy_measurements(self, df=None, normalize=False):
        """Compute the classification accuracies

        Compute the standard accuracy and a custom accuracy. The standard
        accuracy is the number of proposals where the correct category
        is the most probable. The custom accuracy is the number
        of proposals where the correct category is in the top two most probable
        classes.

        Parameters
        ----------
        df
        encoder
        normalie

        Returns
        -------

        """

        custom_accuracy = 0
        custom_accuracy_dict = {}
        if df is None:
            # df = self.
            pass
        # Get the total number of proposals per category
        proposal_numbers = df['hand_classification'].value_counts()
        # Generate a nested dictionary to store the results
        for c in self.encoder.classes_:
            custom_accuracy_dict[c] = {}

        for key in custom_accuracy_dict.keys():
            custom_accuracy_dict[key]['top'] = []
            custom_accuracy_dict[key]['top_two'] = []
            custom_accuracy_dict[key]['misclassified'] = []

        for num, row in df.iterrows():
            hand_classification = row['hand_classification']
            #     print(hand_classification)
            prob_flag = row.index.str.contains('prob')
            top_two = row[prob_flag].sort_values(ascending=False)[:2]
            categories = list(top_two.index)
            categories = [val.replace('_prob', '').replace('_', ' ') for val in
                          categories]

            if hand_classification == categories[0]:
                custom_accuracy_dict[hand_classification]['top'].append(1)
                custom_accuracy += 1
            elif hand_classification in categories:
                custom_accuracy_dict[hand_classification]['top_two'].append(1)
                custom_accuracy += 1
            else:
                custom_accuracy_dict[hand_classification]['misclassified'].append(
                    1
                )
        # Reformat the results so we can generate a dataframe for plotting
        computed_results = {'misclassified': [], 'top_two': [], 'top': []}
        index = []
        for cat in custom_accuracy_dict.keys():
            index.append(cat)
            for key in custom_accuracy_dict[cat].keys():
                num_per_key = sum(custom_accuracy_dict[cat][key])
                if normalize:
                    frac_of_dataset = num_per_key / proposal_numbers[cat]
                else:
                    frac_of_dataset = num_per_key
                computed_results[key].append(frac_of_dataset)
                print(
                    f"Total number of {cat} proposals in {key}: "
                    f"{num_per_key / proposal_numbers[cat]:.2f}"
                )
            print("-"*60)

        self.computed_accuracy = pd.DataFrame(computed_results, index=index)

    def plot_barh(self, df, fout=None):
        """

        Parameters
        ----------
        df

        Returns
        -------

        """
        if fout is None:
            fout = os.path.join(
                self.base,
                f"cy{self.cycle}_accuracy.png"
            )
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6, 5))
        ax = df.plot.barh(
            stacked=True,
            color=['g', 'y', 'r'],
            ax=ax,
            legend=False
        )
        handles, labels = ax.get_legend_handles_labels()
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.legend(handles, labels, bbox_to_anchor=(1., 1.01))#, edgecolor='k')
        ax.set_xlabel('Percentage of Proposals')
        ax.set_title(f'Cycle {self.cycle} Classification Results')
        fig.savefig(fout,
                    format='png',
                    dpi=250,
                    bbox_inches='tight')
        plt.show()

    def plot_barh_all(self, df, fout=None):
        """

        Parameters
        ----------
        df

        Returns
        -------

        """
        if fout is None:
            fout = os.path.join(
                self.base,
                f"pacman_accuracy.png"
            )
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6, 5))
        ax = df.plot.barh(
            stacked=True,
            #color=['g', 'y', 'r'],
            color = ['xkcd:grass green', 'xkcd:goldenrod', 'xkcd:rust'],
            ax=ax,
            legend=False
        )
        handles, labels = ax.get_legend_handles_labels()
        labels=['Top','Top Two', 'Misclassified']
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        #ax.legend(handles, labels, bbox_to_anchor=(1., 1.01), edgecolor='k')
        ax.legend(handles, labels, bbox_to_anchor=(0., 1.02, 1., 0.102), loc='lower left',
                  ncol=3, mode='expand', borderaxespad=0., edgecolor='k')
                  
        ax.set_xlabel('Percentage of Proposals')
        ax.set_ylabel('')
        #ax.set_title(f'PACMan Classification Results')
        fig.savefig(fout,
                    format='png',
                    dpi=250,
                    bbox_inches='tight')
        plt.show()
