# PACMan
The Proposal Auto-Categorizer and Manager (PACMan) is a Naive Bayesian routine that provides tools for science category sorting, panelist selection, and proposal-to-panelist assignments.

### Installation
1. Clone the `PACMan` repo by navigating to a directory where you would like PACMan to be located and doing the following:
`git clone https://github.com/spacetelescope/PACMan`.
2. Create a conda environment with the relevant MacOSX or Linux `yaml` file, eg. `conda env create --file=pacman_osx_3_8.yml`
3. Activate conda environment, eg. `conda activate pacman_osx-3.8`.
4. Install en_core_web_sm with `python3 -m spacy download en_core_web_sm`.
5. Use `run_pacman.py` and scripts in the `PACMan/scripts` repository as below.

### Pre-Requisites
* You will need to acquire and set up an ADS API token/key. Please refer to https://ads.readthedocs.io/en/latest/ for instructions on how to do so, and refer to https://ui.adsabs.harvard.edu/help/api/ for the official documentation of the ADS API.

### Running PACMan from the command line:
1. Edit `config.json` with information about the name of this specific run (`run_name`), which proposal cycles you would like to run PACMan on, which PACMan steps you would like to run, and file naming details.
2. In a terminal, navigate to the `PACMan` directory (`cd PACMan`). Run the primary script with `python run_pacman.py`. This will generate the directory format necessary if it does not already exist. Once the structure is generated, the script will exit with an error message directing the user to input the panelist and proposal data.
3. Place the panelist .csv and proposal text files (see later section of this README for tips on how to convert .pdf files to .txt files) in the relevant directories.
4. Set any steps you'd like to run to `true` in `config.json`.
5. Once again, run the script with `python run_pacman.py`. This will run the steps that you have set to true.
* All output will be generated within a `run_name` folder, which can be found within the `runs_dir` directory (both folders are generated automatically by the script). If `reuse_run` is set to `true` in `config.json`, then subsequent executions of the script with the same instance name (i.e., `run_name` in `config.json`) will reuse any processed output previously generated and stored in the file for `run_name`.  If `reuse_run` is set to `false` when the script is executed again, then any existing `run_name` folder will be moved to the `discard` folder, and a brand-new `run_name` folder and output will be generated.

### Running PACMan with Various Proposal Systems:
While PACMan was originally designed for use with Hubble and JWST proposals, it has been modified such that it can be applied to a wide variety of proposal systems. We encourage using the configuration file to set up proposal-specific information, and we suggest a YYYYMMDD prefix to keep track of the proposal cycles. Also, please note that in addition to updating the `config.json` file, different proposal systems will likely require changes to `scripts/get_science_categories.py` because this contains specific information on science categories and translations between new and old science categories that shifted between one cycle and another cycle of the same proposal system.

### Viewing Pickle Files:
[Pickle](https://docs.python.org/3/library/pickle.html#) is used by PACMan to convert Python object hierarchies into byte streams. If it would be useful to look at any of the `*.pkl` files, we suggest using the following steps:
1. In a terminal, change directories to the location of the `.pkl` file (eg, `cd path/to/file`)
2. Open up ipython (`ipython`)
3. To use pickle, `import pickle` (The `pickle` package should already be installed in your PACMan environment if you used the `yaml` file installation method above. You may need to do a `conda activate pacman_osx-3.8` to activate the environment)
4. Read the `pickle` file using `pickle.load(open('filename.pkl','rb'))`

### Converting PDF to text file:
In order to convert PDF proposals to text files for ingestion into PACMan, we recommend using a package such as PyPDF. You can do this by importing the package: in your terminal, install and import the package with `conda install PyPDF2` and `import PyPDF2`.
First, create a PDF file object with `pdfFileObj = open('example_file.pdf', 'rb')`.
Then, create a PDF reader object with `pdfReader = PyPDF2.PdfFileReader(pdfFileObj)`, create a page object with `pageObj = pdfReader.getPage(0)`, and finally extract the text from that page with `text=pageObj.extractText()`.
Once the pdf has been converted to text, you can close the PDF file object with `pdfFileObj.close()`.
The output `txt` files should be stored in subfolders by cycle within the `input_proposal_data` directory.  The `input_proposal_data` directory will be generated for you when `run_pacman.py` is first executed (as described earlier in this README).

##### Options:
 * --help, -h       : print this help
 * --verbose, -v    : verbose mode
 * --bayes X        : defines a different Bayes file
 * --train          : switch from test/application mode to training mode
 * --authors        : assumes corpus.txt is a list of authors for ADS Crawl default is corpus is text, like science justification
 * --exact_names    : if authors specified, uses exact name match in ADS Crawl
 * --first_author   : if authors specified, uses only first author results from ADS Crawl
 * --nyears X       : specify the number of years past in the abstract bibliography of ADS Crawl
 * --plot           : plot testing results (if aplicable)
 * --hst            : preset for HST proposals

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

### Issues or Feature Requests:
If you encounter any issues, you can check for some more information on how the script ran in the log files located in the `/logs/` directory.
If you still cannot figure out the issue, feel free to contact strolger@stsci.edu or tking@stsci.edu, or submit an issue in this GitHub repository.

### How PACMan works:
Naive Bayesian classification is a popular and effective method for
differentiating between types of documents. In contrast to a simple
frequentist classification, Bayesian classification takes into account
posterior probability, determined by training on pre-classified data-in
this case, Hubble science proposals. During training, each proposal of
known science category is broken down into a 'bag' of its component
words. As these lists of science words are parsed, the classifier builds
a probabilistic model for each word using Bayes' Theorem.

##### Robinson's Method
Once the Bayesian classifier is trained, it is ready to parse new,
unclassified proposals. The data for each word found in a proposal are
combined using Robinson's Method to form an overall probability that the
proposal falls into an established category. The formula combines
p-values from a number of independent tests into one overall p-value
with chi-squared distribution. The results are normalized, yielding a
percent likelihood that the proposal belongs in each category.

##### Improvements
Several measures can be taken in order to make the spam classifier even
more accurate. Words like "a", "the", and "it", which are clearly
unrelated to science categories, are removed before
classification. Conversely, words that are almost always found in only
one science category-"planet" in "Planets", for example-can be used to
prime PACMan before training.

This project is licensed under the terms of the MIT license.
