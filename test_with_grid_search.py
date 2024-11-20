from grid_search import grid_search

# specify which dataset you want to run
subjects = 100
channels = 20

# specify the options
options = {'main_dir': '/Users/ryshum/MATLAB/matlab_signflip/new/',  # location of the data folders
            'method_name': 'Hierarchical', # "Normal" or "Hierarchical"
            'ref_data_available': True,  # set to True if ground-truth data is available; by default = False
            'record_results': 1  # whether you want to obtain results for plots
 }

# run the algorithm
grid_search(subjects=subjects, channels=channels, options=options)
