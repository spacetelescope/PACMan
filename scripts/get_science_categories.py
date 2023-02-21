#!/usr/bin/env python
import os
import glob
import json
import logging
from pylab import *

from scripts import constants as constants
config = constants.config


translate_categories = {
    'solar system astronomy': ['solar system'],
    'exoplanets and exoplanet formation': ['extrasolar planets and planet formation',
                                           'planets and planet formation',
                                           'extra-solar planets',
                                           'debris disks'],
    'stellar physics and stellar types': ['stellar physics', 'hot stars',
                                          'cool stars'],
    'stellar populations and the interstellar medium': ['stellar populations',
                                                        'ism and circumstellar matter',
                                                        'resolved stellar populations',
                                                        'resolved star formation'],
    'intergalactic medium and the circumgalactic medium': ['quasar absorption lines and igm'],
    'supermassive black holes and active galaxies': ['massive black holes and their hosts',
                                                     'massive black holes and their host galaxies',
                                                     'agn/quasars'],
    'galaxies': [],
    'large scale structure of the universe': [],
    }


def parse_scientific_category(file):
    with open(file, 'r') as openfile:
        lines = openfile.readlines()
    #f.close()
    text = ''
    for line in lines:
        if not line.strip():
            continue
        if 'scientific category' in line.strip().lower():
            text += line.strip().lower()+' '
    return(text)


def parse_keywords(file):
    with open(file, 'r') as openfile:
        lines = openfile.readlines()
    #f.close()
    text = ''
    for line in lines:
        if not line.strip():
            continue
        if 'scientific keywords' in line.strip().lower():
            text += line.strip().lower()+' '
    return(text)


def main():
    config = constants.config

    rootdir = os.getcwd()
    workdirs = glob.glob(os.path.join(constants.input_proposal_dir,
                                        config['main_test_cycle']))
    for workdir in workdirs:
        if not os.path.isdir(workdir): continue
        outfile = os.path.join(constants.path_output,
                                (os.path.basename(workdir)
                                +constants.compare_results_by_hand_file))
        #outfile = config['output_dir']+config['main_test_cycle']+config['compare_results_by_hand_file']
        if os.path.isfile(outfile):
            os.remove(outfile)
        fobj = open(outfile, 'w')
        fobj.write('proposal_num,hand_classification\n')
        os.chdir(workdir)
        filecounts = []
        for file in sort(glob.glob('*.txtx')):
            filecounts.append(int(file.split('.')[0]))
        filesuffix = '.'.join(file.split('.')[1:])
        for count in range(5500):
            count += 1
            if count not in filecounts:
                new_cat = 'null'
            else:
                new_cat = []
                file = '%05d' % (int(count))+'.'+filesuffix
                category = parse_scientific_category(file)
                category = category.replace('scientific category: ', '').strip()
                if category in list(translate_categories.keys()):
                    new_cat = category
                elif category not in [val for sublist in list(translate_categories.values()) for val in sublist]:
                    keywords = parse_keywords(file)
                    keywords = keywords.replace('scientific keywords: ', '').strip().split(', ')
                    if ('cosmology' in category) and ('clusters of galaxies' in keywords):
                        new_cat = 'large scale structure of the universe'
                    if (('cosmology' in category) or ('galaxies' in category)) and ('circumgalactic medium' in keywords):
                        new_cat = 'intergalactic medium and the circumgalactic medium'
                    if (('galaxies' in category) or ('galaxy' in category)) and not ('circumgalactic medium' in keywords):
                        new_cat = 'galaxies'
                    if ('cosmology' in category) and not ('circumgalactic medium' in keywords):
                        new_cat = 'large scale structure of the universe'
                    if (category == 'unresolved star formation'):
                        if (('supernovae' in keywords) or ('gamma-ray bursts' in keywords)
                            or ('supernova remnants' in keywords)
                            or ('massive stars' in keywords) or ('circumstellar disks' in keywords)):
                            new_cat = 'stellar physics and stellar types'
                        elif 'clusters of galaxies' in keywords:
                            new_cat = 'large scale structure of the universe'
                        elif 'interstellar and intergalactic medium' in keywords:
                            new_cat = 'stellar populations and the interstellar medium'
                        elif (('galaxy morphology and structure' in keywords)
                              or ('ir-luminous galaxies' in keywords)
                              or ('ir-luminous galaxies,' in keywords)
                              or ('dwarf galaxies' in keywords)
                              or ('starburst galaxies' in keywords)
                              or ('spiral galaxies' in keywords)
                              or ('irregular galaxies' in keywords)):
                            new_cat = 'galaxies'
                        else:
                            logging.info('help!')
                            new_cat = 'null'

                else:
                    for k, v in translate_categories.items():
                        if category in list(v):
                            new_cat = k

                if not new_cat and (category == 'stellar physics stellar physics'):
                    new_cat = 'stellar physics and stellar types'

                if not new_cat:
                    logging.info("issue with new category")
            logging.info('%05d,%s' % (int(count), new_cat))
            fobj.write('%05d,%s\n' % (int(count), new_cat))
        fobj.close()
        os.chdir(rootdir)


if __name__ == '__main__':
    logging.info("Proceeding with get_science_categories")
    main()
