# PACMan
The Proposal Auto-Categorizer and Manager (PACMan) is a Naive Bayesian routine that provides tools for science category sorting, panelist selection, and proposal-to-panelist assignments.

PACMan is currently under development, and the first release is expected in the summer of 2021.

### Installation
1. Clone the `PACMan` repo by navigating to a directory where you would like PACMan to be located and doing the following:
`git clone https://github.com/spacetelescope/PACMan`
2. Create a conda environment with the relevant MacOSX or Linux `yaml` file, eg. `conda env create --file=pacman_osx.yml`.
3. Activate conda environment, eg. `conda activate pacman_macosx`.
4. Install en_core_web_sm with `python3 -m spacy download en_core_web_sm`.
5. Use scripts in the `PACMan/scripts` repository

### Software Contributions
In order to contribute to PACMan, it is best to adhere to the following workflow:
1. Create a fork
2. Make a local clone of your fork
3. Ensure fork is pointing upstream
4. Create a branch off of your fork
5. Make changes
6. Push branch to origin
7. Create a pull request
8. Review and merge changes
9. Delete local copy of branch

### Using Git LFS

Because PACMan utilized numerous large files for training, we recommend using Git's `Large File Storage` capabilities rather than committing large files directly to Git. This uses pointers so that multiple versions of large files are not stored directly on a local machine when the repo is cloned.

##### Steps:
1) From within the PACMan conda environemnt (eg, `conda activate pacman_osx-3.8`), install LFS with `brew install git-lfs`
2) Complete the installation with `git lfs install`
3) In order to tell LFS which files to track, use the command `git lfs track FILENAME`. It may be useful to request that all `.txt`, `.txtx`, `.csv`, and `.pkl` files are tracked, since these tend to be the large files in the PACMan repository. To do so, replace `FILENAME` with `*.txt`, `*.txtx`, `*.csv`, and `*.pkl`.
4) You should be able to see that changes were made to the `.gitattributes` file (you can check this with `git status` or, from the main `PACMan` directory, view the file with `open .gitattributes`.
5) Add the `.gitattributes` file and commit to the repository (eg, `git add .gitattributes`, and then `git commit -m "adding git attributes file"`)

### Running PACMan with Various Proposal Systems:
While PACMan was originally designed for use with Hubble and JWST proposals, we are currently expanding PACMan to be more universal so that it can be applied to a wider variety of proposal systems. We encourage using the configuration file to set up proposal-specific information, and we suggest using a YYYYMMDD prefix to keep track of the proposal cycles. Also, please note that in addition to updating the `config.json` file, different proposal systems will likely require changes to `scripts/get_science_categories.py` because this contains specific information on science categories and translations between new and old science categories that shifted between one cycle and another cycle of the same proposal system. 
