#!/usr/bin/env python

import sys

from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib.backends.backend_pdf import PdfPages
plt.style.use('ggplot')
from matplotlib import colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder



def plot_accuracy_measurements(df, encoder=None, normalize=False):
    """Make a bar plot of classification accuracies

    This will create

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
    # Get the total number of proposals per category
    proposal_numbers = df['hand_classification'].value_counts()
    # Generate a nested dictionary to store the results
    for c in encoder.classes_:
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
                frac_of_dataset = num_per_key/proposal_numbers[key]
            else:
                frac_of_dataset = num_per_key
            computed_results[key].append(frac_of_dataset)
            print(
                f"Total number of {cat} proposals in {key}: "
                f"{num_per_key / proposal_numbers[cat]:.2f}"
            )

    computed_results_df = pd.DataFrame(computed_results, index=index)
    computed_results_df = computed_results_df[
        ['top', 'top_two', 'misclassified']]
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6, 5))
    ax = computed_results_df.plot.barh(
        stacked=True,
        color=['g','y','r'],
        ax=ax,
        legend=False
    )
    handles, labels = ax.get_legend_handles_labels()
    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.legend(handles, labels, bbox_to_anchor=(1., 1.01), edgecolor='k')
    ax.set_xlabel('Number of Proposals')
    fig.savefig('classification_successes_cycle24_raw_test.png',
                format='png',
                dpi=250,
                bbox_inches='tight')
    plt.show()

def plot_probabilities(
        df,
        col1=None,
        col2=None,
        encoder=None,
        cbar_bounds=None,
        marker=None,
        custom_norm=None,
        # use_all=False
):
    prep = lambda val: val.replace('_prob','').replace('_',' ')
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6,5))
    # if use_all:
    #     x = df[col1]
    #     y = df[col2]
    # else:
    #     x = df[df['hand_classification']==]
    scat_ax = ax.scatter(
        df[col1],
        df[col2],
        cmap='Dark2',
        marker='*',
        s=15,
        alpha=0.6,
        c=df['hand_encoded_classification'],
        norm=custom_norm
    )
    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.set_xlabel(
        f"p({prep(col1)})",
        fontsize=10
    )
    ax.set_ylabel(
        f"p({prep(col2)})",
        fontsize=10
    )
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    cbar = fig.colorbar(scat_ax, cax=cax,
                        ticks=cbar_bounds,
                        orientation='vertical')

    cbar_labels = [val for val in encoder.classes_]
    cbar.ax.set_xticklabels(cbar.ax.get_xticklabels(), rotation=45)
    cbar.set_ticks([val + 0.5 for val in cbar_bounds])
    cbar.ax.set_yticklabels(cbar_labels, ha='left', rotation=0, fontsize=8)
    cbar.set_label(r'Hand Classification', fontsize=10)
    ax.set_title(f"p({prep(col1)}) vs p({prep(col2)})", fontsize=10)
    fig.savefig(
        f"{col1.replace('_prob','')}_{col2.replace('_prob','')}.png",
        format='png',
        dpi=250,
        bbox_inches='tight'
    )
    return fig

def plot_training_set_summary(df=None):
    if df is None:
        df = pd.read_csv(
            '/Users/nmiles/PACMan_dist/notebooks/'
            'cycle25_hand_classification_stats.txt',
            header=0
        )
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(6,5))

    proposal_count = df['classification'].value_counts()
    proposal_count.sort_index(inplace=True)
    proposal_count.plot.barh(ax=ax)
    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.set_xlabel('Number of Proposals')
    ax.set_title('Distribution of Categories in Training Set')
    fig.savefig('training_set_stats.png',
                format='png', dpi=250, bbox_inches='tight')

def run_visualization(save_pdf=False, save_barplot=False):
    df = pd.read_csv('/Users/nmiles/PACMan_dist/notebooks/'
                     'cycle_24_classification_results.txt')
    cbar_bounds = [i for i in range(len(set(df['hand_classification']))+1)]

    encoder = LabelEncoder()
    encoder.fit(df['hand_classification'])
    nl = '\n'
    print(f"The identified classes are:\n{nl.join(encoder.classes_)}")
    encoded_values = encoder.transform(df['hand_classification'])
    try:
        assert (df['hand_encoded_classification'] == encoded_values).all()
    except AssertionError as e:
        print(e)
        sys.exit()

    sci_cmap = plt.cm.Dark2
    custom_norm = colors.BoundaryNorm(boundaries=cbar_bounds,
                                      ncolors=sci_cmap.N)

    if save_pdf:
        with PdfPages('probability_comparisons.pdf') as pdf:
            for i, col1 in enumerate(encoder.classes_):
                for j, col2 in enumerate(encoder.classes_):
                    if i != j:
                        fig = plot_probabilities(
                            df=df,
                            col1=col1.replace(' ','_')+'_prob',
                            col2=col2.replace(' ','_')+'_prob',
                            encoder=encoder,
                            cbar_bounds=cbar_bounds,
                            custom_norm=custom_norm
                        )
                        pdf.savefig(fig)
                        plt.close()
        # pdf.close()
    if save_barplot:
        plot_accuracy_measurements(df, encoder=encoder)
    plot_training_set_summary()
    return df


if __name__ == '__main__':
    run_visualization(save_barplot=True)