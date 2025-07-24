import pandas as pd
from find_flip import compute_flip
from flip_data import flip_data
import copy
import random
import numpy as np


def quick_flip(data, T, options, subject_arrangement, covmats=False):
    """
        This function computes the flips in a 'hierarchical' manner.

        :param data: dict of DataFrame, contains the 'ambiguous' data for all subjects
        :param T: numpy.ndarray, no. of time/data points for each subject
        :param options: dict, contains various parameters to set
        :param subject_arrangement: numpy.ndarray, supposed to be arranged in the following way:
        :param covmats: boolean, True if 'data' is an autocorrelation matrix instead of raw data, default=False
        if there are 50 subjects in total, we can create a hierarchy in the following manner:
        [10,2] -> this means that:
        -> divide the 50 subjects into 10 groups (of 5 subjects each) first
        -> then those 10 groups/ 10 super-subjects into 2 groups of 5 subjects each
        Important: for a good accuracy/score each group must have 5 or more subjects - a good example is [10,2] for 50 subjects
        :return: the_flips_matrix: numpy.ndarray, 1's and 0's indicating whether to flip a channel for a subject or not
        """

    # * set default values
    options_flip = {"max_lag": 10,
                    "no_batch": 0,
                    "no_runs": 5,
                    "prob_init_flip": 0.25,
                    "standardize": 1,
                    "partial": 1,
                    "verbose": 1,
                    "max_cyc": 10000,
                    "threshold": 0.00001,
                    "hierarchical_sol": 1,
                    "record_results": False}

    # * we don't need reference_flips for hier. solution
    # * set ref flips to an empty array
    flips_ref = np.array([])

    # * if options are specified, set their values here
    if options is not None:
        for key, value in options.items():
            options_flip[key] = value

    # * dividing into a hierarchy of subject groups
    levels = len(subject_arrangement)  # no of levels in the hierarchical division
    curr_data = data

    helper_dict = {}  # * saves the group info for each level of grouping
    old_T = T
    flip_helper = {}  # * save the flips for each group per level

    # to record results
    if options["record_results"]:
        score_path_per_level = {}
        accuracy_path_per_level = {}  # fixme: unnecessary to plot accuracy

    for level in range(levels):
        # * 1. Creating the GROUPS for the current level
        subjID_list_per_group = make_groups(subject_arrangement=subject_arrangement, level=level, curr_data=curr_data)
        helper_dict[level] = subjID_list_per_group
        no_of_groups = len(subjID_list_per_group)

        # * 2. Obtain data length T for subjects in each group
        new_T_groups = {}  # * to save the data length
        for g in range(no_of_groups):
             new_T_groups[g] = get_T(old_T, helper_dict, g, level=level)

        # * 3. Grouping DATA into the groups created earlier
        data_groups = get_subject_data(data=curr_data, helper_dict=helper_dict, level=level)  # * create data grouping here

        # Computation ------------------------------------------------------------------------------------------
        # * perform computation on each of the groups
        if options["record_results"]:
            score_path_per_group = {}
            accuracy_path_per_group = {}

        flips_per_group = {}
        new_groups = {}
        for g in range(no_of_groups):
            group_data = data_groups[g]
            T = new_T_groups[g]
            if options["record_results"]:
                [flips_per_group[g], score_path_per_group[g], accuracy_path_per_group[g]] = compute_flip(group_data, flips_ref, T, options=options_flip)
            else:
                flips_per_group[g] = compute_flip(group_data, flips_ref, T, options=options_flip)

            # * flip data + combine the subject data in each group into one single "super-subject"
            output_data = flip_data(group_data, T, flips_per_group[g])

            # * save the same group after flipping the signs in that group
            new_groups[g] = output_data

            # change T adequately - data length changes because subjects in a group combine to make a "super-subject"
            new_T_groups[g] = len(new_groups[g])

        # * save the flips for all groups computed in this level
        flip_helper[level] = flips_per_group

        # * in next iteration of 'levels', recompute flips on these super-groups treating each group as a single subject
        curr_data = new_groups
        old_T = new_T_groups

        # * if we want to record results for plotting, save all the groups' results in the current level
        if options["record_results"]:
            score_path_per_level[level] = score_path_per_group
            accuracy_path_per_level[level] = accuracy_path_per_group

    # * compute a flips matrix that caters for all subjects and how many times each subject has been flipped
    the_flips_matrix = flippidydoo(flip_helper=flip_helper, helper_dict=helper_dict)

    if options["record_results"]:
        return [the_flips_matrix, score_path_per_level, accuracy_path_per_level]
    else:
        return the_flips_matrix


def get_subject_data(data, helper_dict, level):
    """
    Once groups have been determined, i.e. which subject belongs to which group, this function then obtains subject
    data and organizes them into the respective 'groups'
    :param data: dict of Dataframe, contains the data grouped into subjects from the previous level
    :param helper_dict: dict, contains the previous and current groupings
    :param level: int, the current level on which we are making groups
    :return: data_for_all_groups: list of dict of Dataframe, data for each subject arranged into the respective groups
    """
    if level == 0:  # * i.e., we're grouping for the first time
        # * obtain the grouping information for the current level
        current_groups = helper_dict[level]
        data_for_all_groups = []  # * list of dicts to hold the data for all the groups in the current level
        for group in range(len(current_groups)):
            subj_list = current_groups[group]
            data_for_curr_group = dict()  # * dict to hold the data for all subs in curr group

            for subject in subj_list:
                curr_sub_data = data[subject]
                data_for_curr_group[subject] = (curr_sub_data)

            data_for_all_groups.append(data_for_curr_group)

    else: # todo repeated here in the if statement
        # * obtain the grouping information for the current level
        current_groups = helper_dict[level]
        data_for_all_groups = []  # * list of dicts to hold the data for all the groups in the current level
        for group in range(len(current_groups)):
            subj_list = current_groups[group]
            data_for_curr_group = dict()  # * dict to hold the data for all subs in curr group

            for subject in subj_list:
                curr_sub_data = data[subject]  # * note: the keys in data start from 0 once we've already made groups
                data_for_curr_group[subject] = (curr_sub_data)

            data_for_all_groups.append(data_for_curr_group)

    return data_for_all_groups


def get_T(T, helper, group, level):
    """
    Once groups are made, this function determines the data length for each subject whose data will be grouped.
    :param T: numpy.ndarray, holds data length (no. of samples) for each subject's data
    :param helper: dict, contains the previous and current groupings
    :param group: int, the current group
    :param level: int, the current level on which we are making groups
    :return: T_for_group: numpy.ndarray, no. of samples for each subject's data in the current group
    """
    groups_in_curr_level = helper[level]

    subjects_in_curr_group = groups_in_curr_level[group]
    # * determine data length for subjects in the group
    T_for_group = np.empty([len(subjects_in_curr_group)])
    for s in range(len(subjects_in_curr_group)):
        T_for_group[s] = T[subjects_in_curr_group[s]]

    return T_for_group


def make_groups(subject_arrangement, level, curr_data):
    """
    Randomly assigns subjects into the groups suggested by subject_arrangement
    :param subject_arrangement: list, gives the info about the hierarchical grouping that the user wants
    :param level: int, current level of grouping
    :param curr_data: dict of Dataframe, data that needs to be grouped
    :return: subjID_list_per_group: dict, info of how many groups are made and which subjects are grouped into which groups
    """
    no_of_groups = subject_arrangement[level]
    sub_per_group = int(len(curr_data) / no_of_groups)
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
            s = s + 1

    subjID_list_per_group = {}  # subject IDs for subs in each group are saved here
    start = 0
    for g in range(no_of_groups):
        # * for all the groups except the first (in some cases), the no. of subjects per group is the same
        end = start + subs_per_group_array[g]
        subjID_list_per_group[g] = randomized_subjects[start:end]  # create subject ID grouping here
        start = end

    return subjID_list_per_group


def flippidydoo(flip_helper, helper_dict):
    """
    Note: I promise I will change the name one day. But not today.
    This function helps generate a final flips matrix "them_flips" once subjects in each group at each level have been flipped.
    It caters for subjects that may have been flipped multiple times.

    :param flip_helper: dict of dict of ndarray, stores the flips for each subject in each group at each level
                        arranged so --> flip_helper[level][group][subject_no, channel_no]
    :param helper_dict: dict, contains all groupings
    :return: them_flips: numpy.ndarray, matrix of 1's and 0's with size = [channels x orig. no. of subjects]
    """
    total_levels = len(helper_dict)
    no_of_subjects = 0
    for groups in range(len(helper_dict[0])): no_of_subjects = no_of_subjects + len(helper_dict[0][groups])
    no_of_channels = flip_helper[0][0].shape[1]
    subject_channel_matrix = np.zeros((no_of_subjects, no_of_channels))

    # * go up in the hierarchy from the lowest level to the first, top-most level of grouping
    for level in range(total_levels)[::-1]:
        no_groups_in_curr_level = len(flip_helper[level])
        for group in range(no_groups_in_curr_level):
            no_of_subjects = len(flip_helper[level][group]) # * could be normal or super-subjects in a group
            for sub in range(no_of_subjects):
                flips_per_sub = flip_helper[level][group][sub]
                channels_flipped = np.where(flips_per_sub == 1)
                if len(channels_flipped[0]) > 0:
                    if level > 0:
                        # * retrieve which smaller subjects this super-subject is composed of
                        subs = retrieve_subjects(helper_dict, level, group, sub)
                    else:  # when we're dealing with subjects in groups at level 0
                        subs = helper_dict[level][group][sub]

                    # * add the no. of times a channel for a subject has been flipped
                    for chans in channels_flipped[0]:
                        subject_channel_matrix[subs, chans] = subject_channel_matrix[subs, chans] + 1
                        #print(chans)

                else:
                    continue

    # * create the binary flips matrix
    them_flips = np.zeros([subject_channel_matrix.shape[0], subject_channel_matrix.shape[1]])
    for subs in range(subject_channel_matrix.shape[0]):
        for channels in range(subject_channel_matrix.shape[1]):
            # * if a subjects' channel has been flipped an even number of times - it ends up not being flipped at all
            if subject_channel_matrix[subs, channels]%2 == 0 or subject_channel_matrix[subs, channels]==0:
                them_flips[subs, channels] = 0
            else:
                them_flips[subs, channels] = 1

    return them_flips


def retrieve_subjects(helper_dict, l, g, s):
    """
    This function retrieves the unit subjects that a super-subject is composed of. This is because once subjects are grouped and the
    algorithm is run on this group, the group is then treated as a "super-subject", and we need to know what "smaller" subjects
    combined to form this "super"-subject
    Usage: flippidydoo()
    :param helper_dict: dict, contains all groupings
    :param l: int, current level for retrieval
    :param g: int, current group
    :param s: int, super-subject ID
    :return: unit_subjects: numpy.ndarray, the subjects that comprise a super-subject
    """
    curr_level = l  # * this is also the number of previous levels
    super_subject = helper_dict[curr_level][g][s]

    prev_level = curr_level - 1
    if prev_level == 0:  # i.e. the first level of grouping
        unit_subjects = helper_dict[prev_level][super_subject]  # * subjects combining to form the current super-subject

    else:
        # the 'super-subject' is the group number in the previous level
        no_of_prev_super_subjects = len(helper_dict[prev_level][super_subject])
        unit_subjects = np.empty((0, 1), dtype=int)
        for subs in range(no_of_prev_super_subjects):
                unit_subs = retrieve_subjects(helper_dict, prev_level, super_subject, subs)
                unit_subjects = np.append(unit_subjects, unit_subs)

    #print(f"Unit Subjects: {unit_subjects}")
    return unit_subjects
