#!/usr/bin/env python

import glob
import logging
import os
import re
import shutil

import tqdm

logging.basicConfig(format='%(levelname)-4s '
                           '[%(module)s.%(funcName)s:%(lineno)d]'
                           ' %(message)s')

LOG = logging.getLogger('proposal_scraper')
LOG.setLevel(level=logging.INFO)

class HSTProposalScraper(object):
    """
    A class for handling the scraping of the text files produced by the pdf to
    ascii converter.

    """

    def __init__(self, for_training=False, cycles_to_analyze=[24, 25]):
        """

        Parameters
        ----------
        for_training : bool
            If True, the scraped proposal are stored in the training data
            directory. If False, they are stored in the unclassified data
            directory
        cycles_to_analyze: list
            List of HST proposal cycle numbers to analyze, e.g. [24, 25]
        """
        self._archival = False
        self._base = os.path.join(
            '/',
            *os.path.dirname(os.path.abspath(__file__)).split('/')[:-1]
        )
        self._cycles_to_analyze = cycles_to_analyze
        self._fname = None
        self._hand_classifications = None
        self._for_training = for_training

        self._proposal_data_dir = os.path.join(
            self.base,
            'proposal_data'
        )

        self._training_dir = os.path.join(
            self.base,
            'training_data'
        )

        self._unclassified_dir = os.path.join(
            self.base,
            'unclassified_proposals'
        )

        self._outdir = None

        self._proposal_label = {
            'Scientific Category': None,
            'Scientific Keywords': None,
        }

        self._section_data = {
            'Abstract': None,
            'Investigators': None,
            'Scientific Justification': None,
            'Science Justification': None,
            'Description of the Observations': None,
            'Special Requirements': None,
            'Justify Duplications': None,
            'Analysis Plan': None
        }

        self._section_data_archival = {
            'Abstract': None,
            'Investigators': None,
            'Scientific Justification': None,
            'Science Justification': None,
            'Analysis Plan': None,
            'Management Plan': None
        }

        self._text = None

    @property
    def archival(self):
        """Flag to specify if proposal is AR or not"""
        return self._archival

    @archival.setter
    def archival(self, value):
        self._archival = value

    @property
    def base(self):
        """Base path of the PACMan package"""
        return self._base

    @base.setter
    def base(self, value):
        self._base = value

    @property
    def fname(self):
        """File to process"""
        return self._fname

    @fname.setter
    def fname(self, value):
        self._fname = value

    @property
    def for_training(self):
        """Boolean switch to indicdate proposals are for training"""
        return self._for_training

    @for_training.setter
    def for_training(self, value):
        self._for_training = value

    @property
    def hand_classifications(self):
        """Path to file containing hand classifications for proposal list"""
        return self._hand_classifications

    @hand_classifications.setter
    def hand_classifications(self, value):
        self._hand_classifications = value

    @property
    def outdir(self):
        """Output directory"""
        return self._outdir

    @outdir.setter
    def outdir(self, value):
        self._outdir = value

    @property
    def proposal_label(self):
        """Keywords to save from the proposal template"""
        return self._proposal_label

    @proposal_label.setter
    def proposal_label(self, value):
        self._proposal_label = value

    @property
    def section_data(self):
        """Section Names defined in the Phase I template"""
        return self._section_data

    @section_data.setter
    def section_data(self, value):
        """Text extracted from the proposal sections for GO, SNAP proposals"""
        self._section_data = value

    @property
    def section_data_archival(self):
        """Text extracted from the proposal sections for AR proposals"""
        return self._section_data_archival

    @section_data_archival.setter
    def section_data_archival(self, value):
        self._section_data_archival = value

    @property
    def text(self):
        """Proposal text"""
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def training_dir(self):
        """Directory to store training data"""
        return self._training_dir

    @training_dir.setter
    def training_dir(self, value):
        self._training_dir = value

    @property
    def unclassified_dir(self):
        """Directory to store unclassified proposal data"""
        return self._unclassified_dir

    @unclassified_dir.setter
    def unclassified_dir(self, value):
        self._unclassified_dir = value

    def read_file(self, fname=None):
        """ Read the file and determine the proposal type

        Parameters
        ----------
        fname : str
            File to process

        Returns
        -------

        """

        if fname is not None:
            self.fname = fname

        with open(self.fname, 'r') as fobj:
            try:
                lines = fobj.readlines()
            except UnicodeDecodeError:
                self._text = None
            else:
                text = [line.strip('\n') for line in lines]
                text = [sentence for sentence in text if sentence]
                text = [
                    re.sub(
                        r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]',' ',sentence
                    )
                    for sentence in text
                ]
                # text = [
                #     re.sub(r'[^a-zA-Z0-9-]+', ' ', sentence)
                #     for sentence in text
                # ]
                self._text = text
                if 'AR' in self.text[1]:
                    self.archival = True
                else:
                    self.archival = False
    def extract_keywords(self):
        """Extract the keyword info above the abstract section

        Returns
        -------

        """
        i=0
        while i < len(self.text):
            for key in self.proposal_label.keys():
                if key in self.text[i]:
                    self.proposal_label[key] = self.text[i].split(':')[-1]
            j = 0
            for key in self.proposal_label.keys():
                if self.proposal_label[key] is not None:
                    j+=1
            if j==2:
                break
            i += 1

    def extract_sections(self, verbose=False):
        """Extract the section data

        Parameters
        ----------
        verbose

        Returns
        -------

        """
        # Set the line number counter
        current_line_num = 0

        # Check to see if the proposal is archival or not and grab
        # the correct section names
        if self.archival:
            section_names = list(self.section_data_archival.keys())
            section_data = self.section_data_archival
        else:
            section_names = list(self.section_data.keys())
            section_data = self.section_data

        # Initialize the current idx for the section_names list
        current_section_idx = 0

        # Initialize a variable for computing the index of the next section.
        # This is required because proposals might be missing sections and so
        # when look for all data between two sections we need to have fine control
        # over what section is used to define the end of the current section
        next_idx = 1

        # Start looping through the text from line 0
        while current_line_num < len(self.text):
            # The current section we are searching for
            current_section = section_names[current_section_idx]

            # Line number corresponding to start and stop of current section
            section_start = None
            section_end = None

            # If we find our section name in the current line number, this
            # begins the start of our section.
            if current_section in self.text[current_line_num]:
                # Section headers have their own line and so the true start is
                # the next index
                section_start = current_line_num + 1
                if verbose:
                    LOG.info(f'{current_section} starts on line {section_start}')

                # Compute the index for the next section in the list 
                next_section_idx = current_section_idx + next_idx
                try:
                    next_section = section_names[next_section_idx]
                except IndexError:
                    # If we've exhausted all section names, write the
                    # remaining portion of the file into the current section
                    if verbose:
                        LOG.info(
                            ('Exhausted all section names, writing remaining'
                             ' lines into current section')
                        )
                    section_end = len(self.text)
                    section_data[current_section] = \
                        self.text[section_start:section_end]
                    break

                # If we haven't exhausted all section names, continue looping
                # through lines until we've found the next section
                j = section_start
                while j < len(self.text):
                    text = self.text[j]
                    # if the next section title is in the current text,
                    # we've found the end
                    if next_section in text:
                        section_end = j - 1
                        if verbose:
                            LOG.info(
                                f'{current_section} ends on line {section_end}'
                            )
                        current_section_idx +=1
                        # Set the current line number to the end of the section
                        # we just found this ensure the loops picks up
                        # on the next section
                        current_line_num = j - 1
                        break

                    # Increase j by one to step to the next line
                    j += 1

                    # If we hit the end of the file and we never found the
                    # current section's end increase the next_idx by one and
                    # search for the next section
                    if j >= len(self.text) and section_end is None :
                        if verbose:
                            LOG.info(
                                (f'Reached the end of file'
                                 f' without finding {next_section}')
                            )
                        j = section_start
                        next_idx +=1
                        next_section_idx = current_section_idx + next_idx
                        try:
                            next_section = section_names[next_section_idx]
                        except IndexError as e:
                            # Exhausted the list again!
                            section_end = len(self.text)
                            current_line_num = section_end
                            break
                        else:
                            if verbose:
                                LOG.info(
                                    (f'Restarting from line {section_start} and '
                                     f'searching for text between {current_section}'
                                     f' {section_names[next_section_idx]}')
                                )
                if verbose:
                    LOG.info(
                        (f'Extracting lines {section_start} to {section_end} '
                         f'for {current_section}')
                    )

                section_data[current_section] = \
                    self.text[section_start:section_end]

                current_section_idx = next_section_idx
                next_idx = 1
            current_line_num+=1
        if self.archival:
            self.section_data_archival = section_data
        else:
            self.section_data = section_data

    def write_training_data(self, cycle, training_sections):
        """ Write out the training data we will use for text classification

        For training, testing, and evaluating we are only interested in the
        Scientific Justification and Abstract of each proposal.

        Parameters
        ----------
        cycle : int
            Proposal Cycle
        training_sections : list
            list of section names to save

        Returns
        -------

        """
        if self.for_training:
            outdir = os.path.join(
                self.training_dir,
                f"training_corpus_cy{cycle}"
            )

        else:
            outdir = os.path.join(
                self.unclassified_dir,
                f"corpus_cy{cycle}"
            )

        try:
            os.mkdir(outdir)
        except FileExistsError:
            pass
        else:
            if self.for_training:
                # LOG.info(f"Copying the hand classifications to {outdir}")
                shutil.copy(self.hand_classifications, outdir)

        fout = os.path.basename(self.fname)
        fout = fout.replace('.txtx', '_training.txt')
        fout = os.path.join(outdir, fout)

        data = []
        for section in training_sections:
            try:
                if self.archival:
                    text = self.section_data_archival[section]
                else:
                    text = self.section_data[section]
                if isinstance(text, list):
                    text = '\n'.join(text)
            except KeyError:
                LOG.info(f'Missing info for {section}')
            else:
                data.append(text)
        #import pdb; pdb.set_trace()
        data = '\n'.join(data)
        with open(fout, mode='w') as fobj:
            fobj.write(data)


    def write_section_data(self, cycle, section_name):
        """ Write out the data for the section specified by section_name

        Parameters
        ----------
        section_name : str

        Returns
        -------

        """
        if self.for_training:
            outdir = os.path.join(
                self.training_dir,
                f"training_corpus_cy{cycle}"
            )
        else:
            outdir = os.path.join(
                self.unclassified_dir,
                f"corpus_cy{cycle}"
            )

        try:
            os.mkdir(outdir)
        except FileExistsError:
            pass

        fout = os.path.basename(self.fname)
        fout = fout.replace(
            ".txtx",
            f"_{section_name.replace(' ', '_')}.txtx"
        )
        fout = os.path.join(outdir, fout)

        try:
            data = self.section_data[section_name]
        except KeyError:
            data = self.proposal_label[section_name]

        if data is None:
            LOG.warning('\nOops! Nothing to write out.\n'
                     'You must execute the .extract_sections() method first.')
        else:
            if isinstance(data, list) :
                data = '\n'.join(data)

            with open(fout, mode='w') as fobj:
                fobj.write(data)


    def extract_flist(self, cycle, flist=None):
        """Extract the Abstract and Scientific Justification sections

        Parameters
        ----------
        flist : list
            List of files to process

        Returns
        -------

        """

        for f in tqdm.tqdm(flist,desc='Scraping Proposals'):
            self.read_file(fname=f)
            if self.text is None:
                continue
            self.extract_sections()
            self.extract_keywords()

            if (not self.archival) and (self.section_data['Scientific Justification'] is None):
            #if (self.section_data['Scientific Justification'] is None):
                self.write_training_data(
                    cycle=cycle,
                    training_sections=['Abstract', 'Science Justification']
                    )
            else:
                self.write_training_data(
                    cycle=cycle,
                    training_sections=['Abstract', 'Scientific Justification']
                    )

    def scrape_cycles(self):
        """ Initiate the scraping for the user supplied proposal cycles

        Returns
        -------

        """
        for cycle in self._cycles_to_analyze:
            path = os.path.join(
                self._proposal_data_dir,
                f"Cy{cycle:02d}_proposals_txt"
            )
            try:
                hand_classifications = glob.glob(
                    f"{path}/cycle_{cycle:.0f}_hand*txt"
                )[0]

            except IndexError:
                if self.for_training:
                    LOG.error(
                        'Proposal data to be used for '
                        'training but no hand classifications were found'
                    )
                    break
            else:
                self.hand_classifications = hand_classifications

            LOG.info(f"{path}/*txtx")
            flist = glob.glob(f"{path}/*txtx")
            if flist is not None:
                LOG.info(f"Found {len(flist)} proposals to scrape")
                self.extract_flist(cycle=cycle, flist=flist)
            else:
                LOG.info(f"No files found at {path} for Cycle {cycle:.0f}")
