import scipy.io
import ast
from pathlib import Path
import numpy as np
import pandas as pd
from IPython.core.debugger import prompt

from find_flip import compute_flip
from flip_data import flip_data
from hierarchical_solution import quick_flip
from plots import create_plots


def compute_and_apply_flips(directory, ref_data_available, low_power_solution, record_results):
    """
    This function computes the "flips" for the data in the passed directory using the proposed
    algorithm and then applies these flips onto the data to provide the "corrected" data.
    :param directory: string showing location of the data
    :param ref_data_available: boolean showing whether ground-truth data is available or not
    :param low_power_solution: boolean showing whether a more efficient, quicker algorithm should be employed
    :param record_results: boolean showing whether the results need to be recorded for plotting later on (default = True)
    :return:
    """

    print('Currently computing solution for the data in folder: ' + str(directory))

    # * a dict to help concatenate the dataframe for each subject
    amb_dict = {}
    sub_no = 0

    # * load sign-ambiguous data
    directory_in_str = Path(directory)
    convention = '**/*ambiguous*.mat'
    matfiles = sorted(Path(directory_in_str).glob(convention), key=lambda path: int(path.stem.rsplit("subject_", 1)[1]))
    for matfile in matfiles:
        path_in_str = str(matfile)
        mat = scipy.io.loadmat(path_in_str)

        struct = mat['my_struct']  # the struct in the .mat file that holds all data
        val = struct[0,0]
        data = val['data']
        df = pd.DataFrame(data)

        # * save this dataframe with the other subjects'
        amb_dict[sub_no] = df
        sub_no = sub_no + 1

    if ref_data_available:
        # * create df for all the original data (not ambiguously flipped)
        convention = '**/*unflipped*.mat'
        orig_files = sorted(Path(directory_in_str).glob(convention), key=lambda path: int(path.stem.rsplit("subject_", 1)[1]))  # read in the original unflipped files
        orig_dict = {}
        sub = 0
        for file in orig_files:
            path_in_str = str(file)
            mat = scipy.io.loadmat(path_in_str)

            # * specify the field name containing the data
            df = pd.DataFrame(mat['data'])
            # * create a dict of dataframes to store all the subject data.
            orig_dict[sub] = df # * appends the original data for each subject to the dict
            sub = sub+1

        # * compute flips_ref (the ground truth flips)
        flips_ref = compute_ref_flips(amb_dict, orig_dict)

    else:
        flips_ref = np.array([])

    # * specifying options  #TODO: ADD VARYING RUNS HERE
    options = {
        "max_cyc": 1000,
        "standardize": 1,
        "record_results": record_results
    }

    # * obtaining ntimepts (T) for each subject
    ntimepts = np.array([])
    for subject in amb_dict.keys():
        ntimepts = np.append(ntimepts, amb_dict[subject].shape[0])

    # * compute flips using the Hierarchical Solution
    if low_power_solution:
        options = {"hierarchical_sol": 1,
                   "max_cyc": 1000,
                   "standardize": 1,
                   "record_results": record_results}

        subject_arr = get_user_input(sub_no) # * the arrangement to group subjects

        if record_results:
            [flips, scores_per_level, accuracies_per_level] = quick_flip(amb_dict, ntimepts, options, subject_arrangement=subject_arr)
            create_plots(scores_per_level, accuracies_per_level, low_power_solution)
        else:
            flips = quick_flip(amb_dict, ntimepts, options, subject_arrangement=subject_arr)

    # * compute flips using normal method
    else:
        if record_results:
            [flips, score, accuracy] = compute_flip(amb_dict, flips_ref, ntimepts, options)
            create_plots(score, accuracy, low_power_solution)
        else:
            #flips = compute_flip(amb_dict, flips_ref, ntimepts, options)
            import cProfile
            profiler = cProfile.Profile()
            flips = profiler.runcall(compute_flip, amb_dict, flips_ref, ntimepts, options)  # con() is actually run here
            profiler.print_stats()
            #flips = cProfile.run('compute_flip(amb_dict, flips_ref, ntimepts, options)')


    # * flipping data
    flipped_data = flip_data(amb_dict, ntimepts, flips)
    print('Data Correctly Flipped')
    # todo: write data to file?


def compute_ref_flips(amb_dict, orig_dict):
    '''
    Computes a matrix of 1's and 0's that shows which channels per subject were flipped ambiguously in
    the "original" data to obtain the "ambiguous" data. This matrix can ultimately be used to compute a measure of accuracy.

    :param amb_dict: contains all the sign-ambiguous data for all subjects
    :param orig_dict: contains original unambiguous data for all subjects
    :return: flips_ref: the [subject x channels] matrix containing 1 for channels that are falsely flipped and 0 otherwise
    '''
    no_chans = amb_dict[1].shape[1]
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