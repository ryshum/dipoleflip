from pathlib import Path
from find_and_flip import compute_and_apply_flips


# Our data is arranged in the following manner:
# For each configuration {i.e., no. of channels , no. of subjects} there exists a folder which contains
# [2*no. of subjects] files. Half of these are the ground-truth/reference files ("unflipped_data_...") and the rest are
# ambiguously-flipped ("..._ambiguous_data") and the algorithm is applied to the latter.
# Currently only .mat files are accepted as input data.


def grid_search(subjects, channels, options):
    # * read in the main directory that contains directories for all possible prob-subject pairs

    # * set default values
    options_grid_search = {"main_dir": Path('.').cwd(),
                    "method_name": 'Normal',
                    "ref_data_available": False,
                    "record_results": 1
                    }

    # * if options are specified, set their values here
    for key, value in options.items():
        options_grid_search[key] = value

    if options_grid_search['method_name'] is None:
        low_power_solution = False
    elif options_grid_search['method_name']  == 'Normal':
        low_power_solution = False
    elif options_grid_search['method_name'] == 'Hierarchical':
        low_power_solution = True


    if subjects is None and channels is None: #todo; need a better solution for when the user doesn't specify subs and chans
        # * to go through the desired data folders
        subjects = [10]  # e.g., subjects = [5, 10, 25, 50]
        channels = [10]  # e.g., channels = [10, 20, 30, 40, 50]

        for sub in subjects:
            for ch in channels:
                folder = 'sub_' + str(sub) + '_ch_' + str(ch)  # * name convention of the folder containing data
                pair_directory = options_grid_search['main_dir']/folder
                ref_data_available = options_grid_search['ref_data_available']
                low_power_solution = options_grid_search['method_name']
                record_results = options_grid_search['record_results']
                compute_and_apply_flips(pair_directory, ref_data_available, low_power_solution=low_power_solution,
                                        record_results=record_results)  # * will compute 'flips' and flip data and print results

    else:  # * when the user specifies the no. of subjects and channels
        folder = 'sub_' + str(subjects) + '_ch_' + str(channels)  # *  name convention of the folder containing data
        pair_directory = options_grid_search['main_dir'] + folder
        ref_data_available = options_grid_search['ref_data_available']
        low_power_solution = True if options_grid_search['method_name']=="Hierarchical" else False
        record_results = options_grid_search['record_results']
        compute_and_apply_flips(pair_directory, ref_data_available, low_power_solution=low_power_solution,
                                record_results=record_results)  # * will compute 'flips' and flip data and print results
