#!/usr/bin/env python
import os
import pickle
import json
import logging

from scripts import constants as constants
config = constants.config


def main():
    logging.info("Proceeding with write_conflicts")
    #configfile = "./config.json"
    #with open(configfile) as data_file:
    #    config = json.loads(data_file.read())

    conflict_file = os.path.join(constants.path_output,
                    (config['main_test_cycle']+constants.conflict_file_suffix))
    with open(conflict_file, 'rb') as openfile:
        data = pickle.load(openfile)
    #outfile = conflict_file.replace('pkl', 'txt')
    outfile = os.path.join(constants.path_output, #config['input_panelist_dir'],
                    (config['main_test_cycle']+constants.conflict_file_suffix)
                    ).replace('pkl', 'txt')
    with open(outfile, 'w') as openfile:
        for k in sorted(data.keys()):
            odict = dict(sorted(data[k].items(), key=lambda item: item[1],
                                reverse=True))
            logging.info('%s-> %s' % (k, odict))
            openfile.write('%s-> \t %s\n' % (k, odict))
    #f.close()


if __name__ == '__main__':
    main()
