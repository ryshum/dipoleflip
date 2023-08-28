import pandas as pd
import copy

def flip_data(data, T, flips):
    """
    Flip the channels of data according to flips obtained from find_flip
    :param data: dict, contains the 'ambiguous' data for all subjects
    :param T: numpy.ndarray, no. of time/data points for each subject
    :param flips: numpy.ndarray, 1's and 0's indicating whether to flip a channel for a subject or not
    :return: output_df: Dataframe, "flipped" or corrected data
    """

    # * TODO: check if data is a dict
    no_subjects = len(data)
    no_channels = data[1].shape[1]
    data_copy = copy.deepcopy(data)

    output_df = pd.DataFrame()

    for sub in range(no_subjects):
        for chan in range(no_channels):
            # * if the value of flips at the sub and chan is 1, flip all data for the sub and chan
            if (flips[sub, chan] == 1):
                data_copy[sub+1].iloc[:, chan] = -data_copy[sub+1].iloc[:, chan]

        output_df = pd.concat([output_df, data_copy[sub+1]])


    return output_df



