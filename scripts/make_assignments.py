#!/usr/bin/env python
import os
import glob
import pickle
import json
from pylab import *
import logging

from scripts import constants as constants
config = constants.config

def main():
    #configfile = "./config.json"
    #with open(configfile) as data_file:
    #    config = json.loads(data_file.read())
    with open(os.path.join(constants.path_output,
                (config['main_test_cycle']
                +constants.assignment_rankings_file_suffix)), 'rb') as openfile:
        rankings = pickle.load(openfile)

    with open(os.path.join(constants.path_output,
                (config['main_test_cycle']
                +constants.conflict_file_suffix)), 'rb') as openfile:
        conflicts = pickle.load(openfile)

    outfile = os.path.join(constants.path_output,
                (config['main_test_cycle']+constants.assignment_outfile_suffix))

    if os.path.isfile(outfile):
        os.remove(outfile)

    with open(outfile, 'w') as openfile:
        new_dict = {}
        files = glob.glob(os.path.join(constants.path_proposals_processed,
                        (config['main_test_cycle']+constants.training_suffix)))
        openfile.write('#proposal_number, recommended_reviewer, cs_score, conflicts(name, num_papers)\n')
        for file in sorted(files):
            tmp = []
            proposal = int(os.path.basename(file)[:5])
            for reviewer in rankings.keys():
                idx = where(rankings[reviewer][:, 0] == proposal)
                try:
                    tmp.append([reviewer, float(rankings[reviewer][idx[0], 1])])
                except:
                    logging.info("error retrieving ranking of reviewer")
            tmp = array(tmp)
            tmp = tmp[tmp[:, 1].argsort()[::-1]]
            new_dict[proposal] = tmp
            for reviewer in tmp[:config['assignment_number_top_reviewers']]:
                openfile.write('%s, "%s", %.2f, ' % (proposal, reviewer[0], float(reviewer[1])))
                close_conflicts = sorted(conflicts[reviewer[0]].items(),
                                         key=lambda x: [x[1], x[0]], reverse=True)
                openfile.write('"')
                for cc, npub in close_conflicts:
                    openfile.write('%s, %d, ' % (cc, int(npub)))
                openfile.write('"')
                openfile.write('\n')
            openfile.write('\n')
    #f.close()


if __name__ == '__main__':
    logging.info("Proceeding with make_assignments")
    main()
