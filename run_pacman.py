#!/usr/bin/env python

from scripts import categorize_one_cycle
from scripts import write_conflicts, make_assignments, train
from scripts import duplication_checker
from scripts import get_science_categories, compare_results_real
from scripts import categorize_ads_reviewers
from scripts import determine_close_collaborators
from scripts import cross_validate

from scripts import constants as constants

from datetime import datetime
import json
import logging
import os
import shutil
from pylab import where, savetxt
import sys

from importlib import reload
reload(logging)


def verify_config(config):
    """Verify the config file contains sufficient variables to run PACMan"""
    # Define the minimum set of variables that must be in the config.json file
    pacman_vars = sorted(constants.config_variables)

    # Identify any PACMan variables missing from the config.json file
    missing_vars = sorted([item for item in pacman_vars if item not in config])

    # Raise an error if any missing variables present
    if len(missing_vars) != 0:
        raise ValueError("Please define the following critical variables in "
                        +"the config.json file:\n{0}".format(missing_vars))

    # Raise an error if any config variables not specified in minimum set (FOR TESTING)
    if (pacman_vars != sorted(list(config.keys()))):
        raise ValueError("Please ensure same variable sets:\n{0}\n{1}"
                .format(
                [item for item in pacman_vars
                        if (item not in list(config.keys()))],
                [item for item in list(config.keys())
                        if (item not in pacman_vars)]))


def verify_setup(config):
    """Verify the setup (e.g., available models) contains sufficient data to run PACMan"""
    # Verify panelist data exists
    if (len(os.listdir(constants.input_panelist_dir)) == 0):
        raise ValueError("Please add panelist data to this directory: {0}"
                        .format(constants.input_panelist_dir))

    # Verify proposal data exists
    if (len(os.listdir(constants.input_proposal_dir)) == 0):
        raise ValueError("Please add proposal data to this directory: {0}"
                        .format(constants.input_proposal_dir))

    # Verify that requested proposal data exists
    all_cycles = sorted(
            [item for item in os.listdir(constants.input_proposal_dir)
            if os.path.isdir(os.path.join(constants.input_proposal_dir, item))])
    # Check for main cycle
    if config['main_test_cycle'] not in all_cycles:
        raise ValueError("Requested main_test_cycle {0} does not exist in "
                        .format(config['main_test_cycle'])
                        +"proposal cycle directory {0}.\nAvailable cycles: {1}"
                        .format(constants.input_proposal_dir, all_cycles))
    # Check for past cycles
    if any([item not in all_cycles for item in config['past_cycles']]):
        raise ValueError("A requested past_cycle in {0} does not exist in "
                        .format(config['past_cycles'])
                        +"proposal cycle directory {0}.\nAvailable cycles: {1}"
                        .format(constants.input_proposal_dir, all_cycles))

    # Verify models exist if train=false
    if (not config['train']) and (not os.path.isdir(config['models_dir'])):
        raise ValueError("There are no existing models. Please train on "
                        +"proposals first ('train'=true in config.json) to "
                        +"train on proposal data and create models.")


def set_log_level(config):
    """Retrieve logging level from configuration file for use in log setup"""
    if config['log_level'] == "info":
        log_level = logging.INFO
    elif config['log_level'] == "debug":
        log_level = logging.DEBUG
    elif config['log_level'] == "warning":
        log_level = logging.WARNING
    elif config['log_level'] == "critical":
        log_level = logging.CRITICAL
    else: # Throw error if unrecognized log form requested
        raise ValueError("Log level {0} not recognized.\nAllowed values: {1}"
                        .format(config['log_level'],
                                ["info", "debug", "warning", "critical"]))
    return log_level


def create_log_file(log_path, run_name, config, log_level, time): #config, log_level):
    """Create a log file to save configuration information
    and output at the level set in the config file"""
    #file_name=config['log_dir']+"PACMan_{}.log".format(time)
    file_name = os.path.join(log_path, "PACMan_{0}_{1}.log"
                                        .format(run_name, time))
    logging.basicConfig(filename=file_name,
                        level=log_level,
                        format='%(levelname)-4s %(asctime)s'
                        '[%(module)s.%(funcName)s:%(lineno)d]'
                        ' %(message)s')
    logging.info("Using the following configuration information: {}".format(config))
    print("Log file can be found at {}".format(file_name))


def create_data_directories(config):
    """Create any necessary input data directories which do not already exist."""

    # If repositories do not exist, create them
    # For folders containing runs, logs, and discards
    run_path = constants.run_path
    log_path = constants.log_path
    discard_path = constants.discard_path
    if not os.path.isdir(config['runs_dir']):
        os.mkdir(config['runs_dir'])
    if not os.path.isdir(log_path):
        os.mkdir(log_path)
    if not os.path.isdir(discard_path):
        os.mkdir(discard_path)

    # For folder containing panelist data
    if ((not os.path.isdir(constants.input_panelist_dir))):
        os.mkdir(constants.input_panelist_dir)
    # For folder containing proposal data
    if ((not os.path.isdir(constants.input_proposal_dir))):
        os.mkdir(constants.input_proposal_dir)


def create_pacman_directories(config, log_level, time):
    """Create any necessary PACMan directories which do not already exist.
    If directories are created and data is needed, script will exit so that user can put in data.
    If correct directories already exist, script will continue running PACMan steps specified."""

    # If repositories do not exist, create them
    run_path = constants.run_path
    log_path = constants.log_path
    discard_path = constants.discard_path

    # For this log and folder containing this run
    if os.path.isdir(run_path): # Throw error if run already exists
        #raise ValueError("This run already exists: {0}. Please delete previous "
        #                .format(run_path)
        #                +"run or change the name of this new run to continue.")
        if config['reuse_run'] == "true":
            print("This run already exists. Previous output will be recycled.")
        else:
            #time = datetime.now().strftime("%Y%m%dT%H%M%S")
            old_path = run_path + "_" + time
            os.rename(run_path, old_path)
            shutil.move(old_path, discard_path)
            print("This run already exists. Previous version moved to {0}."
                    .format(discard_path))
            #else:
            os.mkdir(run_path)
    else:
        os.mkdir(run_path)

    #create_log_file(config, log_level)
    create_log_file(log_path=log_path, run_name=config['run_name'],
                    config=config, log_level=log_level, time=time)

    # Generate internal folders of this run
    if (config['reuse_run'] != "true") or (not os.path.isdir(constants.path_proposals_processed)):
        os.mkdir(constants.path_proposals_processed)
    if (config['reuse_run'] != "true") or (not os.path.isdir(constants.path_output)):
        os.mkdir(constants.path_output)
    if (config['reuse_run'] != "true") or (not os.path.isdir(constants.path_model_results)):
        os.mkdir(constants.path_model_results)
    if (config['reuse_run'] != "true") or (not os.path.isdir(constants.path_duplication_hashes)):
        os.mkdir(constants.path_duplication_hashes)
    if (config['reuse_run'] != "true") or (not os.path.isdir(constants.path_plots)):
        os.mkdir(constants.path_plots)

    # Create model and data folders for training, if necessary
    if config['train'] == "true":
        raise ValueError("Code not ready yet here.")
        #if not os.path.isdir(constants.input_proposal_dir):
        #    os.mkdir(constants.input_proposal_dir)
        if not os.path.isdir(config['models_dir']):
            os.mkdir(config['models_dir'])
        #
        """
        for cycle in config['past_cycles']:
            if not os.path.isdir(config['training_filepath']+cycle):
                os.mkdir(config['training_filepath']+cycle)
            if not os.path.isdir('./'+config['proposal_working_directories']+cycle):
                os.mkdir('./'+config['proposal_working_directories']+cycle)
                need_input_data = True
        if not os.path.isdir(config['training_filepath']+config['main_test_cycle']):
            os.mkdir(config['training_filepath']+config['main_test_cycle'])
            need_input_data = True
        if not os.path.isdir('./'+config['proposal_working_directories']+config['main_test_cycle']):
            os.mkdir('./'+config['proposal_working_directories']+config['main_test_cycle'])
            need_input_data = True
        if not os.path.isdir('./'+config['training_filepath']+config['main_test_cycle']):
            os.mkdir('./'+config['training_filepath']+config['main_test_cycle'])
            need_input_data = True
        """
    #

    logging.info("Repositories have been created as necessary. Running PACMan.")


def run_pacman(config, time):
    # Save a record of the config dictionary as a local config file
    file_configrecord = os.path.join(constants.log_path, "config_{0}_{1}.json".format(config['run_name'], time))
    with open(file_configrecord, 'w') as openfile:
        json.dump(config, openfile, sort_keys=True, indent=4)

    # Run routines specified in config.json
    if config["train"] == "true":  # train the model
        logging.info("Running train.main()")
        train.main()
    if config["categorize_one_cycle"] == "true":  # main tool
        logging.info("Running categorize_one_cycle.main()")
        categorize_one_cycle.main()
    if config["get_science_categories"] == "true":  # additional tool, could use to test consistency of categorization
        logging.info("Running get_science_categories.main()")
        get_science_categories.main()
    if config["compare_results_real"] == "true":  # additional tool
        logging.info("Running compare_results_real.main()")
        compare_results_real.main()
    if config["duplication_checker"] == "true":
        logging.info("Running duplication_checker.main()")
        duplications, corpus = duplication_checker.main()
        idx = where(duplications[:, 2] >= 10)
        ## savetxt(corpus.replace('_hashes.pkl', '_duplications.txt'), duplications[idx], fmt='%s')
        tmpdir = os.path.join(
            constants.path_output,
            os.path.basename(corpus).replace('_hashes.pkl', '_duplications.txt')
            )
        savetxt(tmpdir, duplications[idx], fmt='%s')
        logging.info("... Duplications written to {}".format(tmpdir))
    if config["categorize_ads_reviewers"] == "true":
        logging.info("Running categorize_ads_reviewers.main()")
        categorize_ads_reviewers.main()
    #if config["categorize_ads_reviewers"] == "true":  # determine_close_collaborators dependent on categorize_ads_reviewers
        logging.info("Running determine_close_collaborators.main()")
        determine_close_collaborators.main()
    #if config["categorize_ads_reviewers"] == "true":  # write_conflicts dependent on categorize_ads_reviewers
        logging.info("Running write_conflicts.main()")
        write_conflicts.main()
    #if config["make_assignments"] == "true":
        logging.info("Running make_assignments.main()") # make_assignments dependent on categorize_ads_reviewers and write_conflicts
        make_assignments.main()
    if config["cross_validate"] == "true":
        logging.info("Running cross_validate.main()")
        cross_validate.main()


def main():
    print("Running PACMan...")

    # Gather contents of configuration file
    config = constants.config
    time = datetime.now().strftime("%Y%m%dT%H%M%S") #Time stamp for this run

    # Create input data directories
    create_data_directories(config)

    # Verify config contents are valid
    verify_config(config)

    # Verify sufficient setup for specified run
    verify_setup(config)

    # Set up logging
    log_level = set_log_level(config)

    # Create necessary directories for running PACMan and fill with data if needed
    create_pacman_directories(config=config, log_level=log_level, time=time)

    # Run PACMan steps specified in configuration file:
    run_pacman(config=config, time=time)


if __name__ == '__main__':
    main()
