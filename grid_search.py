from pathlib import Path
from find_and_flip import compute_and_apply_flips

# The simulated data is arranged in the following manner:
# For each configuration {i.e., no. of channels , no. of subjects} there exists a folder which contains
# [2*no. of subjects] files. Half of these are the ground-truth/reference files ("unflipped_data_...") and the rest are
# ambiguously-flipped ("..._ambiguous_data") and the algorithm is applied to the latter.
# Currently only .mat files are accepted as input data.


def grid_search(subjects, channels, options):
    """
    Read in data from the main directory that contains directories for all possible subject-channel pairs e.g. "20_subs_10_chs".
    See comments above.
    :param subjects: list of no. of subjects in the datasets on which sign-flip is to be performed
    :param channels: list of no. of channels in the data files on which sign-flip is to be performed
    :param options: dict of different parameter that will be used to call functions to flip data
    :return:
    """

    # * set default values
    options_grid_search = {"main_dir": Path('.').cwd(),
                    "method_name": 'Normal',
                    "ref_data_available": False,
                    "record_results": True
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

    assert subjects is not None and channels is not None, 'Number of subjects and channels in your data configuration have not been specified'

    for sub in subjects:
        for ch in channels:  # * when the user specifies the no. of subjects and channels
            folder = 'sub_' + str(sub) + '_ch_' + str(ch)  # *  name convention of the folder containing data
            pair_directory = options_grid_search['main_dir'] + folder
            ref_data_available = options_grid_search['ref_data_available']
            low_power_solution = True if options_grid_search['method_name']=="Hierarchical" else False
            record_results = options_grid_search['record_results']
            compute_and_apply_flips(pair_directory, ref_data_available, low_power_solution=low_power_solution,
                               record_results=record_results)  # * will compute 'flips' and flip data and print results
