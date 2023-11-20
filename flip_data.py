import pandas as pd
import numpy as np
import copy

def flip_data(data, T, flips):
    """
    Flip the channels of data according to flips obtained from find_flip
    :param data: dict, contains the 'ambiguous' data for all subjects
    :param T: numpy.ndarray, no. of time/data points for each subject
    :param flips: numpy.ndarray, 1's and 0's indicating whether to flip a channel for a subject or not
    :return: output_df: Dataframe, "flipped" or corrected data
    """

    # * TODO: assert/check if data is a dict
    no_subjects = len(data)
    first_key = next(iter(data))
    no_channels = data[first_key].shape[1]
    data_copy = copy.deepcopy(data)

    output_df = pd.DataFrame()

    # * if we're doing hierarchical stuff, the subject IDs/keys would be random
    subject_keys = np.array(list(data.keys()))
    subject_list = subject_keys

    print(subject_list)

    for sub in range(len(subject_list)):
        for chan in range(no_channels):
            subj_key = subject_list[sub]
            # * if the value of flips at the sub and chan is 1, flip all data for the sub and chan
            if flips[sub, chan] == 1:
                data_copy[subj_key].iloc[:, chan] = -data_copy[subj_key].iloc[:, chan]

        output_df = pd.concat([output_df, data_copy[subj_key]])

    print("Done Flipping")
    return output_df



