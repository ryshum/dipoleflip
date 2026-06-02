from pathlib import Path
import re
from simple_test import run_test
import scipy
import numpy as np
import os

## e.g. score = 'Global' / hierarchical_sol = 0 / no_runs = 5
user_specified_options = {"max_lag": 10,
                          "no_batch": 0,
                          "no_runs": 5,
                          "prob_init_flip": 0.25,
                          "standardize": 1,
                          "partial": 1, # set to 1 to compute partial correlation between channels, otherwise normal
                          "verbose": 1,
                          "max_cyc": 10000,
                          "threshold": 0.001,
                          "hierarchical_sol": 0, # set to 1 if you want to run the low-power solution
                          "record_results": False,  # whether you want to obtain results for plotting later on
                          "score_type": 'Global'}

## Reduced dataset (N = 3) from 'taskMEG_Chiara_oddball/raw continuous_reduced'
out = run_test(main_dir = '/home/oliburta/dipoleflip/taskMEG_Chiara_oddball/raw continuous_reduced',
               ref_data_available = False,
               data_type = '.mat',
               file_naming_convention = ['subj'],
               user_specified_options = user_specified_options,
               data_storage_convention='subject',
               transp = True)

print(out[0]) # flips matrix
print(out[1]) # flipped data
print(out[2]) # matfiles (since we need their paths to save the flipped data in a next step)

##############################################################################################

## Save flipped data at another location
def save_flipped_data(raw_files, sf_data, transpose, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for sub_idx, file in enumerate(raw_files):
        path_in_str = str(file)
        print(path_in_str)
        mat = scipy.io.loadmat(path_in_str)
        print(np.shape(mat["subject"])) # todo this is hard-coded
        print(sf_data)
        old_data = mat["subject"]

        df_to_replace = sf_data[sf_data['subject'] == sub_idx].drop(columns='subject')
        new_data = df_to_replace.to_numpy()

        if transpose:
            new_data = new_data.T

        try:
            if old_data.shape != new_data.shape:
                raise ValueError(
                    f"Shape mismatch for subject {sub_idx}: "
                    f"old {old_data.shape}, new {new_data.shape}"
                )

            mat["subject"] = new_data

        except Exception as e:
            print(f"[ERROR] subject {sub_idx}: {e} \n(have you transposed the data?)")
            continue

        ### Save files
        filepath_to_save = os.path.join(out_dir, os.path.basename(file))
        scipy.io.savemat(filepath_to_save, mat)
        print(f'File saved at {filepath_to_save}')



save_flipped_data(raw_files = out[2],
                  sf_data = out[1],
                  transpose = True,   # todo: this should be carried over from the input to run_test()
                  out_dir = '/home/oliburta/dipoleflip/taskMEG_Chiara_oddball/sflipped continuous_reduced')