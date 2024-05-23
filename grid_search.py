from pathlib import Path
from find_and_flip import compute_and_apply_flips

# Our data is arranged in the following manner:
# For each configuration {i.e., no. of channels , no. of subjects} there exists a folder which contains
# [2*no. of subjects] files. Half of these are the ground-truth/reference files ("unflipped_data_...") and the rest are
# ambiguously-flipped ("..._ambiguous_data") and the algorithm is applied to the latter.
# Currently only .mat files are accepted as input data.


def grid_search(subjects, channels, method_name):
    # * read in the main directory that contains directories for all possible prob-subject pairs
    main_dir = Path('.').cwd()
    # main_dir = Path('/Users/ryshum/Python/dipole_flip/data_sim')  # TODO: specify in cmd line?

    if method_name is None:
        low_power_solution = False
    elif method_name == 'Normal':
        low_power_solution = False
    elif method_name == 'Hierarchical':
        low_power_solution = True
    ref_data_available = True  # set to True if ground-truth data is available; by default = False

    if subjects is None and channels is None:
        # * to go through the desired data folders
        subjects = [10]  # e.g., subjects = [5, 10, 25, 50]
        channels = [10]  # e.g., channels = [10, 20, 30, 40, 50]

        for sub in subjects:
            for ch in channels:
                folder = 'sub_' + str(sub) + '_ch_' + str(ch)  # * mention the name convention of the folder containing data
                pair_directory = main_dir/folder
                compute_and_apply_flips(pair_directory, ref_data_available, low_power_solution=low_power_solution)  # * will compute 'flips' and flip data and print results

    else:  # * when the user specifies the no. of subjects and channels
        folder = 'sub_' + str(subjects) + '_ch_' + str(channels)  # * mention the name convention of the folder containing data
        pair_directory = main_dir / folder
        compute_and_apply_flips(pair_directory, ref_data_available, low_power_solution=low_power_solution)