from find_flip import compute_flip
from flip_data import flip_data
import copy
import random
import numpy as np

def quick_flip(data, flips_ref, T, options, subject_arrangement):
    """
        This function computes the flips in a 'hierarchical' manner.

        :param data: dict of DataFrame, contains the 'ambiguous' data for all subjects
        :param flips_ref: numpy.ndarray, array of 1's and 0's to show whether a channel for a subject was flipped in the "original" dataset
        :param T: numpy.ndarray, no. of time/data points for each subject
        :param options: dict, contains various parameters to set
        :param subject_arrangement: numpy.ndarray, supposed to be arranged in the following way:
        if there are 50 subjects in total, we can create a hierarchy in the following manner:
        [10,2,1] -> this means that:
        -> divide the 50 subjects into 10 groups (of 5 subjects each) first
        -> then those 10 groups/ 10 super-subjects into 2 groups
        -> then those 2 groups/ 2 super-super-subjects combined into 1 group or 1 super-super-super-subject (not suggested)
        Important: each group must have 5 or more subjects - a good example is [10,2] for 50 subjects
        :return: flips: numpy.ndarray, 1's and 0's indicating whether to flip a channel for a subject or not
        """

    # * set default values
    options_flip = {"max_lag": 10,
                    "no_batch": 0,
                    "no_runs": 5,
                    "prob_init_flip": 0.25,
                    "standardize": 1,
                    "partial": 0,
                    "verbose": 1,
                    "max_cyc": 10000,
                    "threshold": 0.00001}

    # * if options are specified, set their values here
    for key, value in options.items():
        options_flip[key] = value

    # * dividing into a hierarchy of subject groups
    levels = len(subject_arrangement)  # no of levels in the hierarchical division
    curr_data = copy.deepcopy(data)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for level in range(levels):
        no_of_groups = subject_arrangement[level]
        sub_per_group = int(len(curr_data)/no_of_groups)
        subs_per_group_array = np.ones((no_of_groups), dtype=int) * sub_per_group

        # * randomize the subjects in groups
        no_of_subjects = len(curr_data)
        randomized_subjects = np.arange(no_of_subjects)
        random.shuffle(randomized_subjects)

        # * split the data into equal groups and treat each group as a single subject at a time
        # * if the no. of subjects is not a multiple of the no. of groups, add in extra subjects in the groups
        if len(curr_data) % no_of_groups > 0:
            over_booked = len(curr_data) % no_of_groups
            s = 0
            for i in range(over_booked):
                subs_per_group_array[s] = subs_per_group_array[s] + 1
                s = s+1

        # - DATA ------------------------------------------------------------------------------------------
        # * create groups in the subject data
        groups = {}
        start = 0
        for g in range(no_of_groups):
            # * for all the groups except the first (in some cases), the no. of subjects per group is the same
            end = start + subs_per_group_array[g]
            groups[g] = get_subject_data(curr_data, start, end, randomized_subjects)
            start = end

        # - GROUND-TRUTH and T (Data length)---------------------------------------------------------------------------
        # * if ground-truth data is present, divide that into respective groups as well
        # * if this is the first level, arrange reference flips in a dict
        if flips_ref.size > 0:
            if level == 0:
                flipsr_dict = dict(enumerate(flips_ref, 1))
                T_list = dict(enumerate(T, 1))

            # * if this is the second level or after, flips_ref need to be determined from the prev level
            elif level > 0:
                # * organize the reference_data_groups into the new group arrangement
                flipsr_dict = reference_data_groups
                T_list = T_groups

            # * group all the reference-flips and T-values
            start = 0
            T_groups = {}
            reference_data_groups = {}
            for g in range(no_of_groups):
                end = start + subs_per_group_array[g]
                reference_data_groups[g] = get_ref_flips_dict(flipsr_dict, start, end, randomized_subjects)
                T_groups[g] = get_T(T_list, start, end, randomized_subjects)
                start = end

        # * In case reference flips isn't present------------------------------------------------------------
        # - T - DATA LENGTH only
        else:
            if level == 0:
                T_list = dict(enumerate(T, 1))
                reference_data_groups = {}
            else:
                T_list = T_groups

            # * for all groups
            T_groups = {}
            start = 0
            for g in range(no_of_groups):
                end = end + subs_per_group_array[g]
                T_groups[g] = get_T(T_list, start, end, randomized_subjects)
                start = end

        # Computation------------------------------------------------------------------------------------------
        # * perform computation on each of these groups
        flips_per_group = {}
        new_groups = {}
        for g in range(no_of_groups):
            group_data = groups[g]
            flips_r = get_ref_flips_array(reference_data_groups[g])
            T = T_groups[g]
            flips_per_group[g] = compute_flip(group_data, flips_r, T, options=options)

            # * flip data + combine the subject data in each group into one single "super-subject"
            output_data = flip_data(group_data, T, flips_per_group[g])

            # * save
            new_groups[g] = output_data

            # change T adequately
            T_groups[g] = len(new_groups[g])

        # * in next iteration of 'levels', recompute flips on these super-groups treating each group as a single subject
        curr_data = new_groups

    return flips_per_group



def get_subject_data(data, start, end, randomized_list):
    """
    Organizes the data into groups of required no. of subjects
    :param data: dict, subject data
    :param start: int, the starting point of the group of subjects to put into the current group
    :param end: int, the end point
    :param randomized_list: np.ndarray, an array of the subject IDs randomly shuffled
    :return: res_dict: dict, the data for the required subjects arranged into a dict

    """
    all_sub_data = list(data.values())
    required_sub_data = randomized_list[start:end]

    # * convert back to dict from list
    res_dict = {}
    for i in range(1, len(required_sub_data)+1):
        subject_id = required_sub_data[i-1]
        res_dict[i] = all_sub_data[subject_id]

    return res_dict


def get_ref_flips_dict(flipsr, start, end, randomized_list):
    """
    Returns a dictionary of 'flips' after taking the 'flips' array as an input
    :param flipsr: np.ndarray, flips array of size [subjects x channels]
    :param start: int, the starting point of the group of subjects to put into the current group
    :param end: int, the end point
    :param randomized_list: np.ndarray, an array of the subject IDs randomly shuffled
    :return: flips_dict: dict, the 'flips' for the required subjects arranged into a dict
    """
    all_flips = list(flipsr.values())
    required_sub_data = randomized_list[start:end]

    # * convert back to dict from list
    flips_dict = {}
    for i in range(1, len(required_sub_data) + 1):
        subject_id = required_sub_data[i - 1]
        flips_dict[i] = all_flips[subject_id]

    return flips_dict


def get_ref_flips_array(flips_group):
    """
           Returns an array of 'reference flips' values after taking the 'flips_group' dict as an input.
           This dict contains the reference flips for all the subjects in the current group. The function is required because
           the 'compute_flips' function only takes an np.ndarray of reference flips as input.
           :param flips_group: dict, the 'ref flips' for the all subjects in a particular group
           :return: flips_array: np.ndarray, the 'reference flips' arranged into a numpy array
           """
    no_of_subs = len(flips_group)
    no_of_chans = len(flips_group[1])
    flips_array = np.zeros((no_of_subs, no_of_chans), dtype=int)
    for i in range(len(flips_group)):
        flips_array[i, :] = flips_group[i+1].tolist()

    return flips_array


def get_T(T, start, end, randomized_list):
    """
        Returns a dictionary of 'T' values or data length of each subject after taking the 'T' array as an input
        :param T: np.ndarray, ata length of each subject
        :param start: int, the starting point of the group of subjects to put into the current group
        :param end: int, the end point
        :param randomized_list: np.ndarray, an array of the subject IDs randomly shuffled
        :return: T_dict: dict, the 'T' for the required subjects arranged into a dict
        """
    all_T = list(T.values())
    required_sub_data = randomized_list[start:end]

    no_of_subs = len(required_sub_data)
    T_array = np.zeros((no_of_subs, 1), dtype=int)
    for i in range(len(required_sub_data)):
        subject_id = required_sub_data[i]
        T_array[i] = all_T[subject_id]

    return T_array