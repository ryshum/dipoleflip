import scipy.io
from pathlib import Path
import numpy as np
import pandas as pd
from find_flip import compute_flip
from flip_data import flip_data
from hierarchical_solution import quick_flip


def compute_and_apply_flips(directory, ref_data_available, low_power_solution):
    """
    This function computes the "flips" for the data in the passed directory using the proposed
    algorithm and then applies these flips onto the data to provide the "corrected" data.
    :param directory: location of the data
    :param ref_data_available: boolean showing whether ground-truth data is available or not
    :param low_power_solution: boolean showing whether a more efficient, quicker algorithm should be employed
    :return:
    """

    print('Currently computing the data in: ' + str(directory))

    # * a dict to help concatenate the dataframe for each subject
    amb_dict = {}
    sub_no = 0

    # * load sign-ambiguous data
    directory_in_str = Path(directory)
    matfiles = sorted(Path(directory_in_str).glob('**/*_ambiguous_data.mat'))
    for matfile in matfiles:
        path_in_str = str(matfile)
        mat = scipy.io.loadmat(path_in_str)

        struct = mat['S']  # specify the struct in the .mat file that holds all data and info
        struct_fields = struct.dtype  # get names of the fields in the struct

        # * for convenience make dictionary using field names
        struct_data = {n: struct[n][0, 0] for n in struct_fields.names}

        # * specify the data field and get data from the struct and arrange in dataframe
        df = pd.DataFrame(struct_data['data'])

        # * save this dataframe with the other subjects'
        amb_dict[sub_no] = df  # TODO: should change the key to a simpler subject number
        sub_no = sub_no + 1

    # * concatenate all subjects into single dict of df
    pd.concat(amb_dict)

    if (ref_data_available == 1):
        # * create df for all the original data (not ambiguously flipped)
        orig_files = sorted(Path(directory_in_str).glob('**/*unflipped*.mat'))  # read in the original unflipped files
        orig_dict = {}
        sub = 0
        for file in orig_files:
            path_in_str = str(file)
            mat = scipy.io.loadmat(path_in_str)

            # * specify the field name containing the data
            df = pd.DataFrame(mat['X_MAR'])
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
        "standardize": 1
    }

    # * obtaining ntimepts (T) for each subject
    ntimepts = np.array([])
    for subject in amb_dict.keys():
        ntimepts = np.append(ntimepts, amb_dict[subject].shape[0])

    # * compute flips
    if low_power_solution == True:
        options = {"hierarchical_sol": 1,
                   "max_cyc": 1000,
                    "standardize": 1}
        subject_arr = [4,2]  # * the arrangement to group subjects
        flips = quick_flip(amb_dict, ntimepts, options, subject_arrangement=subject_arr)
    else:
        flips = compute_flip(amb_dict, flips_ref, ntimepts, options)

    # * flipping data
    flipped_data = flip_data(amb_dict, ntimepts, flips)
    print('Data Correctly Flipped')




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
            if np.array_equal(orig, amb) == False:
                flips_ref[s, chan] = 1

    return flips_ref