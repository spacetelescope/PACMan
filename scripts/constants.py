#!/usr/bin/env python

# External imports
import os
import json

# Config file
with open("./config.json") as data_file:
    config = json.loads(data_file.read())

# Constant global variables for use by PACMan scripts
# For file paths
run_path = os.path.join(config['runs_dir'], config['run_name'])
log_path = os.path.join(config['runs_dir'], config['log_folder'])
discard_path = os.path.join(config['runs_dir'], "discard")
input_panelist_dir = os.path.join(config['runs_dir'], "input_panelist_data")
input_proposal_dir = os.path.join(config['runs_dir'], "input_proposal_data")
path_proposals_processed = os.path.join(run_path, "processed_proposal_data")
path_output = os.path.join(run_path, "store")
path_model_results = os.path.join(run_path, "model_results")
path_duplication_hashes = os.path.join(run_path, "duplication_hashes")
path_plots = os.path.join(run_path, "plots")
# For internal strings
compare_results_by_hand_file = "_hand_classifications.txt"
comparison_outfile = "_recategorization.txt"
assignment_rankings_file_suffix = "_panelists_match_check.pkl"
assignment_outfile_suffix = "_assignments.txt"
authorfile_suffix = "_panelists.csv" # Must end in .csv
conflict_file_suffix = "_panelists_conflicts.pkl"
duplication_hashes_suffix = "_hashes.pkl"
training_suffix = "/*_training.txt"
cross_validate_savefile = "saved_corpora_cross_validate.pkl"
# For internal booleans
conf_matrix = True
load_model = False
load_file = False

# Minimum config.json variables necessary to run PACMan
#config_variables = sorted(["runs_dir", "run_name", "log_level", "log_folder", "models_dir", "input_proposal_dir", "train", "categorize_one_cycle", "modelfile", "main_test_cycle", "get_science_categories", "compare_results_real", "duplication_checker", "categorize_ads_reviewers", "determine_close_collaborators", "write_conflicts", "make_assignments", "cross_validate", "duplication_checker_newcycles", "past_cycles"])
config_variables = sorted(["reuse_run", "runs_dir", "run_name", "log_level", "log_folder", "models_dir", "train", "categorize_one_cycle", "modelfile", "main_test_cycle", "get_science_categories", "compare_results_real", "duplication_checker", "categorize_ads_reviewers", "cross_validate", "duplication_checker_newcycles", "past_cycles", "close_collaborator_time_frame", "assignment_number_top_reviewers", "duplication_checker_need_new_texts", "help"])

# Class information
class_names = ['Exopl.', 'Gal.', 'IGM', 'LSS', 'Sol.', 'Stars', 'StPops', 'AGN']

# Proposal scraping
scraper_cycles_to_analyze = "None"
is_nress = "false"




#
