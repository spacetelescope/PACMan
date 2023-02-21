#!/usr/bin/env python
import os
import json
import pandas as pd
import logging

from scripts import constants as constants
config = constants.config


def main():
    config = constants.config

    pacman_file = os.path.join(constants.path_model_results, config['modelfile']
                                ).replace('.joblib', '.txt')
    by_hand_file = os.path.join(constants.path_output,
                                (config['main_test_cycle']
                                +constants.compare_results_by_hand_file))
    #f = open(config['output_dir']+config['main_test_cycle']+config['comparison_outfile'], 'w')
    filename = os.path.join(constants.path_output,
                    (config['main_test_cycle']+constants.comparison_outfile))
    with open(filename, 'w') as openfile:
        openfile.write('#propid,pacman_cat,orig_cat,certainty\n')

        data_pacman = pd.read_csv(pacman_file)
        data_by_hand = pd.read_csv(by_hand_file)
        for index_pacman, row in data_pacman.iterrows():
            propid = int(os.path.basename(row['fname']).split('.')[0].split('_')[0])
            cat_pacman = row['encoded_model_classification']
            cat_pacman_n = row['model_classification']
            score_pacman = row[3+cat_pacman]
            index_by_hand = [idx for idx, s in enumerate(data_by_hand['proposal_num']) if propid == s][0]
            cat_by_hand = data_by_hand['hand_classification'][index_by_hand]
            if cat_pacman_n != cat_by_hand:
                # logging.info(propid, index_pacman, index_by_hand, cat_pacman_n, cat_by_hand, score_pacman)#, score_by_hand)
                logging.info('%05d, \"%s\", \"%s\", %.2f' % (propid, cat_pacman_n, cat_by_hand, score_pacman))
                openfile.write('%05d, \"%s\", \"%s\", %.2f\n'
                            % (propid, cat_pacman_n, cat_by_hand, score_pacman))
                #f.write('%05d, \"%s\", \"%s\", %.2f\n' % (propid, cat_pacman_n, cat_by_hand, score_pacman))
    #f.close()


if __name__ == '__main__':
    logging.info("Proceeding with compare_results_real")
    main()
