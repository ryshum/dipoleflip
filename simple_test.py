import scipy.io
from pathlib import Path
import numpy as np
from find_flip import get_global_variables_for_bitflip_eval, compute_flip
from hierarchical_solution import quick_flip
from plots import create_plots

def run_test():
    # specify the options
    main_dir = '/Users/ryshum/MATLAB/matlab_signflip/fake_simulated/' # location of the data folders
    ref_data_available = False  # set to True if ground-truth data is available; by default = False
    data_type = '.mat' # set to either '.mat' or '.npy'

    # * default values to input to the find_flip.py
    user_specified_options = {"max_lag": 10,
                    "no_batch": 0,
                    "no_runs": 5,
                    "prob_init_flip": 0.25,
                    "standardize": 1,
                    "partial": 0, # set to 1 to compute partial correlation between channels, otherwise normal
                    "verbose": 1,
                    "max_cyc": 10000,
                    "threshold": 0.001,
                    "hierarchical_sol": 0, # set to 1 if you want to run the low-power solution
                    "record_results": False,  # whether you want to obtain results for plotting later on
                    "score_type": 'Global'}  # "Pairwise" or "Global"

    #  todo add the naming convention for your data variable in the .mat file

    # run the algorithm
    grid_search(main_dir, data_type, ref_data_available, options=user_specified_options)


def grid_search(main_dir, data_type, ref_data_available, options):

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
                    "hierarchical_sol": 0,
                    "record_results": False,
                    "score_type": 'Global'}

    # * if options are specified, set their values here
    for key, value in options.items():
        options_flip[key] = value

    print('Currently computing solution for the data in folder: ' + main_dir)

    # * load the ambiguous data (that needs to be flipped)
    directory_in_str = Path(main_dir)
    if data_type == '.mat':
        convention = '**/*.mat' # designed to load all .mat files in the specified directory
        matfiles = sorted(Path(directory_in_str).glob(convention))
        ntimepts = [] # for obtaining ntimepts (T) for each subject
        n_subjects = len(matfiles)
        all_covmats = []

        # * construct autocorrelation matrix for the raw data
        for matfile in matfiles:
            path_in_str = str(matfile)
            mat = scipy.io.loadmat(path_in_str)
            mat = mat['data'] # todo change the convention as per user's input
            T = max(mat.shape) # get the number of samples or timepts in the data
            ntimepts.append(T)
            covmat_per_subj = get_global_variables_for_bitflip_eval(mat, T, options_flip)
            all_covmats.append((covmat_per_subj))

        # * convert the list of all covmats into a 4D np array
        covmat_data = np.concatenate(all_covmats, axis=0)

        # * construct reference flips if available
        if ref_data_available:
            # todo do something here
            raise ValueError('Did not implement the case where user has their own defined reference data for flips.')
        else:
            flips_ref = np.array([])

    else:  # if the data is in .npy files
        print("NUMPY FILES") # todo fix this

    # * compute flips using the Hierarchical Solution
    if options_flip['hierarchical_sol'] == '1':
        subject_arr = get_user_input(n_subjects) # * the arrangement to group subjects

        if options_flip['record_results']:
            [flips, scores_per_level, accuracies_per_level] = quick_flip(covmat_data, ntimepts, options, subject_arrangement=subject_arr, covmats=True)
            create_plots(scores_per_level, accuracies_per_level, low_power_solution=True)
        else:
            flips = quick_flip(covmat_data, ntimepts, options, subject_arrangement=subject_arr, covmats=True)

    # * compute flips using normal method
    else:
        if options_flip['record_results']:
            [flips, score, accuracy] = compute_flip(covmat_data, flips_ref, ntimepts, options, covmats=True)
            create_plots(score, accuracy, low_power_solution=False)
        else:
            flips = compute_flip(covmat_data, flips_ref, ntimepts, options, covmats=True)



def compute_ref_flips(amb_dict, orig_dict):
    '''
    Computes a matrix of 1's and 0's that shows which channels per subject were flipped ambiguously in
    the "original" data to obtain the "ambiguous" data. This matrix can ultimately be used to compute a measure of accuracy.

    :param amb_dict: contains all the sign-ambiguous data for all subjects
    :param orig_dict: contains original unambiguous data for all subjects
    :return: flips_ref: the [subject x channels] matrix containing 1 for channels that are falsely flipped and 0 otherwise
    '''
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
                raise Exception(f"The absolute values for Channel {chan+1} for Subject {s+1} in the ambiguous and ground-truth data are not equal")
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