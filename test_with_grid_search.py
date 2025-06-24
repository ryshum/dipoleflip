from grid_search import grid_search

# specify which dataset you want to run
subjects = 25
channels = 30

# specify the options
options = {'main_dir': '/Users/ryshum/MATLAB/matlab_signflip/new/',  # location of the data folders
            'method_name': 'Normal', # "Normal" or "Hierarchical"
            'ref_data_available': True,  # set to True if ground-truth data is available; by default = False
            'record_results': True,  # whether you want to obtain results for plots
           'score_type': 'Global', # "Pairwise" or "Global"
           'partial': 1 # set to 1 to compute partial correlation between channels, otherwise normal
 }

# run the algorithm
grid_search(subjects=subjects, channels=channels, options=options)