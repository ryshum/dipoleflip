import scipy.io
from pathlib import Path
import numpy as np
import pandas as pd
from find_flip import get_global_variables_for_bitflip_eval, compute_flip
from flip_data import flip_data ### Olivier
from hierarchical_solution import quick_flip
from plots import create_plots
import re

    # todo also let the user specify how the data is stored within the .mat (extra parameter)

def run_test(main_dir, ref_data_available, data_type, file_naming_convention, data_storage_convention, transp, user_specified_options):

    print('Providing inputs')

    # todo add a naming convention check for your data variable in the .mat file
    # run the algorithm
    return grid_search(main_dir, data_type, ref_data_available, file_naming_convention, data_storage_convention, transp, options=user_specified_options)


def grid_search(main_dir, data_type, ref_data_available, file_naming_convention, data_storage_convention, transp, options):
    # * default values to input to the find_flip.py
    options_flip = {"max_lag": 10,
                    "no_batch": 0,
                    "no_runs": 5,
                    "prob_init_flip": 0.25,
                    "standardize": 1,
                    "partial": 0,
                    "verbose": 1,
                    "max_cyc": 10000,
                    "threshold": 0.001,
                    "hierarchical_sol": 1,
                    "record_results": False,
                    "score_type": 'Global'}

    # * if options are specified, set their values here
    for key, value in options.items():
        options_flip[key] = value

    print('Currently computing solution for the data in folder: ' + main_dir)

    # if no naming convention has been specified for the files
    assert (file_naming_convention), "No naming convention has been specified for the files."

    # * load the ambiguous data (that needs to be flipped)
    directory_in_str = Path(main_dir)
    if data_type == '.mat':
        conv = file_naming_convention[0] # ambiguous data naming convention specified by the user
        convention = f'**/*{conv}*.mat' # designed to load all .mat files with the specific naming convention in the specified directory

        # todo improve logic
        if ref_data_available == False: # use all files contained in main_dir
            directory_in_str = Path(main_dir)
            matfiles = list(directory_in_str.iterdir())
            # sort by subject number
            matfiles = sorted(matfiles, key=lambda x: int(re.search(r'\d+', x.stem).group()))
        else:
            matfiles = sorted(Path(directory_in_str).glob(convention), key=lambda path: int(path.stem.rsplit("subject_", 1)[1]))

        ntimepts = [] # for obtaining ntimepts (T) for each subject
        n_subjects = len(matfiles)

        if options_flip["hierarchical_sol"] != 1:
            all_covmats = []

        amb_dict = {}  # in case we need to compute reference flips
        sub_no = 0

        # * construct autocorrelation matrix for the raw data
        for matfile in matfiles:
            path_in_str = str(matfile)
            mat = scipy.io.loadmat(path_in_str)

            # todo: sharpen logic, because this can differ quite a lot across users and datasets
            mat = mat[data_storage_convention] # e.g. mat["subject"] or mat["data"][0,0]
            # * option to transpose the data if required
            if transp == True:
                mat = mat.T

            ## mat = mat["my_struct"]["data"][0,0]  # this is for my simulated old data
            #mat = mat['data'] # todo change the convention as per user's input

            T = np.shape(mat)[0] # get the number of samples or timepts in the data
            ntimepts.append(T)

            # normal method - we compute the AC matrix before
            if options_flip["hierarchical_sol"] != 1:
                covmat_per_subj = get_global_variables_for_bitflip_eval(mat, T, options_flip)
                all_covmats.append((covmat_per_subj))

            # * to compute the reference flips, we need to arrange the ambiguous data into dataframe
            df = pd.DataFrame(mat)
            amb_dict[sub_no] = df
            sub_no = sub_no + 1

        # * convert the list of all covmats into a 4D np array
        if options_flip["hierarchical_sol"] != 1:
            covmat_data = np.concatenate(all_covmats, axis=0)

        # * construct reference flips if available
        if ref_data_available:
            if len(file_naming_convention) == 2:
                conv = file_naming_convention[1]
                convention = f'**/*{conv}*.mat'  # user specifies how to identify the reference files in their data
            else:
                raise ValueError("No naming convention has been supplied to identify the reference or 'unflipped' files.")

            directory_in_str = Path(main_dir)  # the unflipped data should be located in the same directory as the ambiguous data
            matfiles = sorted(Path(directory_in_str).glob(convention), key=lambda path: int(path.stem.rsplit("subject_", 1)[1]))
            no_unflip_files = len(matfiles)
            assert no_unflip_files == n_subjects, "Number of 'ambiguous' files are not equal to the number of 'unflipped' files in the specified directory."

            sub_no = 0  # best to start the numbering of subjects from 0
            ref_dict = {}  # the dict of Dataframe that holds all the patient data - ground truth
            for matfile in matfiles:
                path_in_str = str(matfile)
                mat = scipy.io.loadmat(path_in_str)

                data = mat["data"]  # the struct in the .mat file that holds all data

                # * get data from the struct and arrange in dataframe
                df = pd.DataFrame(data)

                # * save this dataframe with the other subjects'
                ref_dict[sub_no] = df
                sub_no = sub_no + 1

            flips_ref = compute_ref_flips(amb_dict, ref_dict)
            # raise ValueError('Did not implement the case where user has their own defined reference data for flips.')
        else:
            flips_ref = np.array([])

    else:  # if the data is in .npy files
        raise ValueError("Did not implement the case where we are able to read .npy files") # todo fix this

    # * compute flips using the Hierarchical Solution - we do not use the Autocorrelation matrix here but raw data
    if options_flip['hierarchical_sol'] == 1:
        subject_arr = get_user_input(n_subjects) # * the arrangement to group subjects

        if options_flip['record_results']:
            [flips, scores_per_level, accuracies_per_level] = quick_flip(amb_dict, ntimepts, options, subject_arrangement=subject_arr)
            create_plots(scores_per_level, accuracies_per_level, low_power_solution=True)
        else:
            flips = quick_flip(amb_dict, ntimepts, options, subject_arrangement=subject_arr)

    # * compute flips using normal method
    else:
        if options_flip['record_results']:
            [flips, score, accuracy, time] = compute_flip(covmat_data, flips_ref, ntimepts, options, covmats=True)
            create_plots(score, accuracy, time, low_power_solution=False)
        else:
            flips = compute_flip(covmat_data, flips_ref, ntimepts, options, covmats=True)

        return flips, flip_data(amb_dict, T, flips), matfiles



def compute_ref_flips(amb_dict, orig_dict):
    '''
    Computes a matrix of 1's and 0's that shows which channels per subject were flipped ambiguously in
    the "original" data to obtain the "ambiguous" data. This matrix can ultimately be used to compute a measure of accuracy.

    :param amb_dict: contains all the sign-ambiguous data for all subjects
    :param orig_dict: contains original unambiguous data for all subjects
    :return: flips_ref: the [subject x channels] matrix containing 1 for channels that are falsely flipped and 0 otherwise
    '''

    # * assert first whether the shapes of the arrays are as required
    assert isinstance(amb_dict, dict), "To compute the reference flips, the 'ambiguous' data needs to be organised into a dict."
    assert isinstance(orig_dict, dict), "To compute the reference flips, the 'unflipped' reference data needs to be organised into a dict."

    no_chans = amb_dict[0].shape[1]
    no_subs = len(amb_dict.keys())
    flips_ref = np.zeros((no_subs, no_chans))

    for s in range(0, no_subs):
        for chan in range(no_chans):
            orig = orig_dict[s][chan].to_numpy()
            amb = amb_dict[s][chan].to_numpy()

            # check if we're even reading the data for the same subject and channel
            # the abs value of the array isn't equal - error
            if np.array_equal(np.absolute(orig), np.absolute(amb)) is False:
                raise Exception(f"The absolute values for Channel {chan+1} for Subject {s+1} in the ambiguous and ground-truth data are not equal. Please check data.")
            else:
                if np.array_equal(orig, amb) == False:
                    flips_ref[s, chan] = 1

    return flips_ref

def get_user_input(max_value):
    """
    Prompts the user to define the groupings of subjects in each level of hierarchical division to speed up computation.
    :param max_value: total number of subjects in the dataset.
    :return:
    """
    PINK = '\033[95m'  # Light magenta
    RESET = '\033[0m'  # Reset to default
    initial_prompt = (f"{PINK}You chose to run the code in a Hierarchical manner. Please specify the number of groups you want the subjects to be divided into at each level.\n"
              "Make sure the number of groups are less than the total number of subjects.\n"
             "For example, if you would want to divide 80 subjects into 20 groups first, then those 20 into 10 groups,\nand then the 10 groups into 2 in the next level "
             "you would enter: 20, 10, 2.\n")

    print(initial_prompt)
    prompt = f"Enter numbers separated by commas (e.g., 20,10,2): {RESET}"
    while True:
        user_input = input(prompt)
        try:
            numbers = [int(x.strip()) for x in user_input.split(',')]
            if all(n < max_value for n in numbers):
                return numbers
            else:
                print(f"Number of groups must be less than the total number of subjects: {max_value}. Try again.")
        except ValueError:
            print("Please enter only numbers separated by commas.")