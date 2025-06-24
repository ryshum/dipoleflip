import copy
import numpy as np
import random
import pandas as pd
from scipy.stats import zscore

def compute_flip(data, flips_ref, T, options):
    """
    This function uses the concept of maximising the sum of all partial correlations to find the most appropriate combination
    of "flips". It runs the greedy search "options['no_runs']" number of times with each run having "options['max_cyc']" cycles
    that run until score converges.
    :param data: dict of DataFrame, contains the 'ambiguous' data for all subjects
    :param flips_ref: numpy.ndarray, array of 1's and 0's to show whether a channel for a subject was flipped in the "original" dataset
    :param T: numpy.ndarray, no. of time/data points for each subject
    :param options: dict, contains various parameters to set
    :return: flips: numpy.ndarray, 1's and 0's indicating whether to flip a channel for a subject or not
    """

    # * assert/check if data is a dict of dfs
    assert dict(data), "Data should be a 'dict' of Dataframes containing data for all subjects"

    # * set default values
    options_flip = {"max_lag": 10,
                    "no_batch": 0,
                    "no_runs": 5,
                    "prob_init_flip": 0.25,
                    "standardize": 1,
                    "partial": 0,
                    "verbose": 1,
                    "max_cyc": 10000,
                    "threshold": 0.001,
                    "hierarchical_sol": 0,
                    "record_results": False,
                    "score_type": 'Global'}

    # * if options are specified, set their values here
    if len(options) > 0:
        for key, value in options.items():
            options_flip[key] = value

    # * get uncorrected, unflipped autocorrelation matrix - [subj x lags x channels x channels]
    covmats_unflipped = get_global_variables_for_bitflip_eval(data, T, options_flip)

    # * if reference flips (i.e. ground truth data) isn't available, set to true
    if flips_ref.size == 0:
        no_ref_flips = True
    else:
        no_ref_flips = False

    no_subjects = covmats_unflipped.shape[0]
    no_channels = covmats_unflipped.shape[2]
    score = -float('Inf')

    score_path = list()  # * holds score for all runs
    accuracy_path = list() # * holds the accuracy for all runs
    assert float(options_flip['max_cyc']) != float('inf') and options_flip['no_batch'] <= 0, 'If max_cyc is inf, no_batch must be 0'

    # * performing greedy search
    for runs in range(options_flip['no_runs']):
        score_path_per_run = np.empty([1,1])

        # * computing initial score (without flipping any channel for any subject)
        flips_per_run = init_solution(no_subjects, no_channels, options_flip, runs+1)
        score_r = evaluate_flips(flips_per_run, covmats_unflipped, sub=None, chan=None, options=options_flip)

        # * adding the initial score to the overall score matrix/path
        score_path_per_run[0] = score_r

        # * compute accuracy only if reference flips are present
        if not no_ref_flips:
            accuracy_path_per_run = np.empty([1, 1])
            accuracy = get_accuracy(flips_per_run, flips_ref)
            # * adding the initial accuracy to the accuracy matrix
            accuracy_path_per_run[0] = accuracy

        if options_flip['verbose'] == 1:
            if not no_ref_flips:
                print('Run ' + str(runs) + ' Initial Score ' + str(score_r) + ' Initial Accuracy ' + str(accuracy))
            else:
                print('Run ' + str(runs) + ' Initial Score ' + str(score_r))

        # * running greedy search to improve score
        for cyc in range(options_flip['max_cyc']):
            if options_flip['no_batch'] > 0:
                channels = random.sample(range(1, no_channels), options_flip['no_batch'])
            else:
                channels = random.sample(range(0, no_channels), no_channels)

            score_matrix = np.zeros((no_subjects, no_channels))

            for ch in channels:
                for sub in range(no_subjects):
                    score_matrix[sub, ch] = evaluate_flips(flips_per_run, covmats_unflipped, sub, ch, options_flip)

            score_r = np.amax(score_matrix)  # * take max of scores for all channel & subject combinations
            max_sub, max_channel = np.where(score_matrix == score_r) # * channel and subject where score is max

            score_diff = score_r - np.max(score_path_per_run)  # * diff b/w the curr score and the max score in the path
            if score_diff > options_flip['threshold']:
                flips_per_run[max_sub, max_channel] = 1 - flips_per_run[max_sub, max_channel]  # * invert 0 to 1 or vice versa
                score_path_per_run = np.append(score_path_per_run, score_r)  # * append when score is greater than previous

                # * compute accuracy
                if not no_ref_flips:
                    accuracy = get_accuracy(flips_per_run, flips_ref)
                    accuracy_path_per_run = np.append(accuracy_path_per_run, accuracy)

                if options_flip['verbose'] == 1:
                    if not no_ref_flips:
                        print('Run '+str(runs)+' Cycle '+str(cyc)+' Score '+str(score_r)+' Accuracy '+str(accuracy)+' Flipped channel: '+str(max_channel)+' Flipped subject: '+str(max_sub))
                    else:
                        print('Run ' + str(runs) + ' Cycle ' + str(cyc) + ' Score ' + str(score_r) +' Flipped channel: '+str(max_channel)+' Flipped subject: '+str(max_sub))

            elif options_flip['no_batch'] == 0:
                break

            else:
                print('Run '+str(runs)+' Cycle '+str(cyc))
                print('No increase in score in the current cycle')

        # * append the scores for this run to the arrays for all runs
        score_path.append(score_path_per_run)

        # * append accuracies
        if not no_ref_flips:
            accuracy_path.append(accuracy_path_per_run)

        # * if greatest score (end of score_path) is greater than -inf
        if score_path_per_run[-1] > score:
            score = score_path_per_run[-1]
            flips = flips_per_run

    # when all runs finish print final score
    if options_flip['verbose'] == 1:
        print ('Final Score: ' + str(score))

    # among the equiv flips, keep ones with the lowest no. of flips
    for subs in range(no_subjects):
        if np.mean(flips[subs]) > 0.5:
            flips[subs] = 1 - flips[subs]

    # do we want to get iterations vs. score vs. accuracy plots
    if options_flip["record_results"]:
        return [flips, score_path, accuracy_path]
    else:
        return flips


def get_global_variables_for_bitflip_eval(data, T, options):
    """
    Constructs an initial, uncorrected, unflipped Autocorrelation Matrix/Tensor with size [subjects x lags x channels x channels].
    :param data: dict, contains the 'ambiguous' data for all subjects
    :param T: numpy.ndarray, no. of time/data points for each subject
    :param options: dict, contains various parameters already set
    :return: covmats_unflipped: numpy.ndarray, autocorrelation matrix for all subjects with lags embedded; size = (subjects x lags x channels x channels)
    """
    # * Prepare necessary data structures
    # * check if data is already an array of autocorrelation matrices
    first_key = next(iter(data))
    if data[first_key].ndim == 3:
        return data  # return data as the covmats_unflipped
    else:
        return get_all_cov_mats(data, options)  # returns covmats_unflipped


def get_all_cov_mats(data, options):
    """
    Processes & standardizes the data before it can be lag-embedded to obtain the Autocorrelation Matrix.
    :param data: dict, contains the 'ambiguous' data for all subjects
    :param options: dict, contains various parameters already set
    :return: covmats_unflipped: numpy.ndarray, autocorrelation matrix for all subjects with lags embedded; size = (subjects x lags x channels x channels)
    """

    no_subjects = len(data.keys())
    X_norm_all_sub = {} # * save all subjects' normalized data here

    # * if we're performing hierarchical solution, the keys of the subject-data dict will be random
    if options["hierarchical_sol"]:
        subject_list = np.array(list(data.keys()))
    else:
        subject_list = np.arange(0, no_subjects)

    # * if standarization needs to be performed
    if options["standardize"]:
        for subnum in subject_list:
            X = data[subnum].to_numpy()

            # * compute mean over each channel
            mean_x = np.mean(X, axis=0)
            # * subtract mean out of each channel time point
            X_norm_mean = np.subtract(X, mean_x)

            # * compute standard deviation for each channel
            std_X = np.std(X_norm_mean, axis=0)
            # * check whether any std value is zero
            assert np.all(std_X), "At least one channel has variance = 0"
            # * otherwise continue to normalize data - element-wise division by stdev
            X_norm_std = np.divide(X_norm_mean, std_X)

            # * need to save it in a single dict for all patients
            X_norm_all_sub[subnum] = X_norm_std

    # * get covmats unflipped
    covmats_unflipped = get_cov_mats(X_norm_all_sub, options)

    return covmats_unflipped


def get_cov_mats(X_norm, options, *flips):
    """
    Gets the autocorrelation matrices upto the specified 'maxlag', for each trial.
    :param X_norm: dict, the standardized, 'ambiguous' data for all subjects
    :param options: dict, contains various parameters already set
    :param flips: numpy_ndarray, 1's and 0's specifying whether to flip a channel or not
    :return: covmats_copy: numpy.ndarray, autocorrelation matrix that has all lags incorporated; size = (subjects x lags x channels x channels)
    """
    no_subject = len(X_norm.keys())
    first_key = next(iter(X_norm))
    no_channels = X_norm[first_key].shape[1]
    max_lag = options["max_lag"]

    # * if flips aren't specified, create an array of zeros
    if flips == ():
        flips = np.zeros((no_subject, no_channels))

    # * create an empty covariance matrix
    covmats = np.zeros((no_subject, 2*max_lag + 1, no_channels, no_channels))
    covmats_copy = copy.deepcopy(covmats)
    eps = 10 ** -8

    # again, if we're doing hierarchical stuff, the subject IDs/keys would be random
    if options["hierarchical_sol"]:
        subject_list = np.array(list(X_norm.keys()))
    else:
        subject_list = np.arange(0, no_subject)

    for sub in range(len(subject_list)):  # goes from 0 to N-1 and not according to subject id/key
        for chan in range(no_channels):  # goes from 0 to 19 for example
            subject_key = subject_list[sub]
            if flips[sub, chan] == 1:
                X_norm[subject_key][chan] = -X_norm[subject_key][chan]

        covmats[sub, :, :, :] = lowmem_xcorr(X_norm[subject_key], max_lag, options)

        for lags in range(2*max_lag + 1):
            # * extract the diagonal of the covariance matrix for the current lag value
            diag = np.diagonal(covmats[sub, lags, :, :]).copy()
            unit_matrix = np.eye(no_channels)
            np.fill_diagonal(unit_matrix, diag)

            # * subtract the diagonal from the cov matrix for each lag, for each subject
            covmats_copy[sub, lags, :, :] = np.subtract(covmats[sub, lags, :, :], unit_matrix)

    return covmats_copy  # return to 'get_all_cov_mats'


def lowmem_xcorr(X_norm, max_lag, options):
    """
    Function to computed correlation using the lag-embedded data.
    :param X_norm: numpy_ndarray, single subject data after being standardized
    :param max_lag: int, number of lags to be implemented in the data
    :param options: dict, contains various parameters already set
    :return: final: numpy.ndarray, lag-embedded data - size = (lags x channels x channels)
    """

    no_channels = X_norm.shape[1]
    no_samples = X_norm.shape[0]

    lags = np.arange(-max_lag, max_lag+1, 1)
    embedded_data = circshift_embed_data(X_norm, no_samples, lags)

    # * compute pairwise partial correlations bw a pair of channels - controlling for other channels
    if options['partial']:
        col_names = ["ch_" + str(i) for i in np.arange(embedded_data.shape[1])]
        df = pd.DataFrame(data=embedded_data, columns=col_names)

        partial_corr = df.pcorr().round(3)
        corr = partial_corr.to_numpy()
    else:
        # * compute Pearson correlation of embedded data
        corr = np.corrcoef(embedded_data, rowvar=False)

    # *
    no_lags = 2*max_lag + 1

    # * create an anti-diagonal matrix
    anti_diag = np.eye(no_lags)[::-1]

    # help_dict = {}  # to hold the new submatrices created
    final = np.zeros((no_lags, no_channels, no_channels))

    for chan in range(no_channels):
        row_start = chan*no_lags
        row_end = chan*no_lags + no_lags

        for chan_2 in range(no_channels):
            col_start = chan_2*no_lags
            col_end = chan_2*no_lags + no_lags
            sub_corr_matrix = corr[row_start:row_end, col_start:col_end]

            # * gives values lying on the anti-diagonal of sub_corr_matrix
            sub_corr_comb = sub_corr_matrix[anti_diag.astype(bool)]

            # * create a new [channel x channel] matrix for each value
            for entry in range(len(sub_corr_comb)):
                # new_matrix = np.zeros((no_channels, no_channels, no_lags))
                # new_matrix[chan, chan_2] = sub_corr_comb[entry]
                final[entry, chan_2, chan] = sub_corr_comb[entry]

    return final  # return this to 'get_cov_mats'


def embed_data(X_norm, no_samples, lags):
    """
    Embeds lags in the data - causality respecting.
    :param X_norm: numpy.ndarray, single subject data after being standardized
    :param no_samples: int, number of time/data points for the current subject
    :param lags: numpy.ndarray, array of lags; lags = 2*max_lag + 1
    :return: X: numpy.ndarray, lag-embedded data ; size = ((no_samples-maxlag) x no_channels*lags)
    """
    no_channels = X_norm.shape[1]
    lags = np.array(lags)
    min_lag = np.min(lags)
    max_lag = np.max(lags)
    L = len(lags)

    # Define the common time range where all lagged versions are valid
    start = -min_lag
    end = no_samples - max_lag
    T_valid = end - start  # number of valid time points

    # Pre-allocate output matrix
    X_lagged = np.zeros((T_valid, no_channels * L))

    for i, lag in enumerate(lags):
        # Shift the data by lag relative to the valid center region
        X_slice = X_norm[start + lag : end + lag, :]  # shape: (T_valid, no_channels)
        X_lagged[:, i * no_channels : (i + 1) * no_channels] = X_slice

    return X_lagged


def circshift_embed_data(X_norm, no_samples, lags):
    """
    REDUNDANT!!!!
    Embeds lags in the data. todo: delete
    :param X_norm: numpy.ndarray, single subject data after being standardized
    :param no_samples: int, number of time/data points for the current subject
    :param lags: numpy.ndarray, array of lags; lags = 2*max_lag + 1
    :return: X: numpy.ndarray, lag-embedded data ; size = (no_samples x no_channels*lags)
    """
    no_channels = X_norm.shape[1]
    no_trials = 1

    # * an array of zeros - size = (no.of samples - time points in lag) x (channels * len(lags))
    shape_X = ((no_samples - (len(lags)-1)), (no_channels * len(lags)))
    X = np.zeros(shape_X)

    # * loop over all samples in a trial (for each subject from get_cov_mats) (todo: maybe implement later)
    for s in range(no_trials): # loop can be removed unless we have data with multiple trials
        # * perform embedding (embedx.m)
        shape_Xe = ((no_samples), (no_channels*len(lags)))
        X_e = np.zeros(shape_Xe)

        for lag in range(len(lags)):
            X_e[:, lag:shape_Xe[1]:len(lags)] = np.roll(X_norm, lags[lag], axis=0)

        # * removing edge effects
        valid = np.ones((no_samples, 1))
        valid[no_samples+min(lags):] = 0
        valid[0:max(lags)] = 0

        # * keeping only the valid values in X_e
        X_e_valid = X_e[max(lags):(no_samples - max(lags)), :]

        # * valid = ind ; X_e_valid = x -> embedx.m MATLAB code comparison
        X[:no_samples-(len(lags)-1), :] = X_e_valid

    return X # return the embedded data


def init_solution(no_subjects, no_channels, options, runs):
    '''
    Creates a randomly -initialized "flips" matrix with 1's and 0's.
    :param no_subjects: int
    :param no_channels: int
    :param options: dict, contains various parameters already set
    :param runs: int, the current run that the greedy search is performing
    :return: flips_r: numpy.ndarray, suggested flips matrix to be applied onto the autocorrelation matrix
    '''

    # * checks whether 'options' has a field 'flips'
    if not 'flips' in options:
        if runs == 1:  # if this is the first run with no flips
            flips_r = np.zeros((no_subjects, no_channels))  # create an array to save flips
        else:
            # * else generate samples from a binomial distribution
            flips_r = np.random.binomial(1, options['prob_init_flip'], size=(no_subjects, no_channels))
    else:
        flips_r = options['flips']

    return flips_r


def evaluate_flips(flips_per_run, covmats_unflipped, sub, chan, options):
    """
    Evaluates the change in flips for subject 'sub' and channel 'chan'
    :param flips_per_run: numpy.ndarray, flips matrix for the current run
    :param covmats_unflipped: numpy.ndarray, autocorrelation matrix
    :param sub: int, the subject whom we flip the channel 'chan' for
    :param chan: int, the channel we want to flip
    :param options: dict, contains various parameters already set
    :return: score: float, the sum of all partial correlations
    """
    flips_r = np.copy(flips_per_run)
    if not (sub is None and chan is None):  # when the subject and channel number have been specified
        # * NOT operation at the specified sub and chan location - portrays "flipping"
        flips_r[sub, chan] = 1 - flips_r[sub, chan]

    # * [subject x channel x channel]
    sign_matrix = get_sign_matrix(flips_r)

    # * apply sign matrices on the auto-correlation matrix
    covmats_copy = np.copy(covmats_unflipped)
    covmats = apply_sign(covmats_copy, sign_matrix)

    # * obtain the score - sum of all correlations
    if options['score_type'] == 'Pairwise':
        score = get_pairwise_score(covmats)
    elif options['score_type'] == 'Global':
        score = get_global_score(covmats)
    return score


def get_sign_matrix(flipsr):
    """
    Constructs matrices that contain "flip-signs" to apply onto the AC matrix.
    :param flipsr: numpy.ndarray, flips matrix for the current run
    :return: sign_matrix: numpy.ndarray, a matrix of 1's and -1's that is applied onto the AC matrix to 'flip' the values
    """
    no_subject = flipsr.shape[0]
    no_channel = flipsr.shape[1]

    sign_matrix = np.zeros((no_subject, no_channel, no_channel))

    for sub in range(no_subject):
        flips_curr = np.ones((no_channel))
        flips_curr[flipsr[sub, :] == 1] = -1

        # compute the transpose of flips_curr
        flips_t = flips_curr[..., None]

        sign_matrix[sub, :, :] = flips_t * flips_curr

    return sign_matrix


def apply_sign(covmats_unflipped, sign_matrix):
    """
    Applies the sign matrices onto the AC matrix.
    :param covmats_unflipped: numpy.ndarray, the autocorrelation matrix
    :param sign_matrix: numpy.ndarray, a matrix of 1's and -1's that is applied onto the AC matrix to 'flip' the values
    :return: covmats_unflipped: numpy.ndarray, the autocorrelation matrix with its respective channel values 'flipped'
    """
    no_subject = covmats_unflipped.shape[0]
    no_lags = covmats_unflipped.shape[1]
    for sub in range(no_subject):
        covmats_unflipped[sub, :, :, :] = covmats_unflipped[sub, :, :, :] * (np.tile(sign_matrix[sub, :, :], (no_lags, 1, 1)))
        # * np.tile repeats the unflipped cov for the curr sub a total of 'no_lags' times
    return covmats_unflipped


def get_pairwise_score(covmats):
    """
    Computes the pairwise score i.e. comparison of inter-subject consistency for each channel pair separately.
    :param covmats: The autocorrelation matrix/tensor [subjects x lags x channels x channels]
    :return: score: A score value that is the sum of all partial correlations.
    """
    no_subject = covmats.shape[0]
    no_channel = covmats.shape[2]
    no_elem = (no_channel**2 - no_channel) * ((no_subject * (no_subject-1))/2)

    score_matrix = np.zeros((no_subject, no_subject, no_channel, no_channel))
    score = 0

    for row in range(no_channel):
        for col in range(no_channel):
            if row != col:
                M_new = covmats[:,:,col,row]
                # * normalise each subject's lag vector
                M_new = zscore(M_new, axis=1, ddof=1)
                C = np.matmul(M_new, np.transpose(M_new))
                C[np.diag_indices_from(C)] = 0  # set all diag elements to zero
                score_matrix[:,:,col,row] = C
                score = score + np.sum(np.triu(C))

    score = score/no_elem
    return score

def get_global_score(covmats):
    """
    Computes the global autocorr score which measures inter-subject similarity by correlating
    each subject's full autocovariance structure as opposed to a single pair of channels.
    :param covmats: Autocovariance tensor of shape [subjects x lags x channels x channels]
    :return: score: Mean correlation between all subject pairs
    """
    no_subjects = covmats.shape[0]

    # * reshape to [subjects x features] where features = channels * channels * lags
    X = covmats.transpose(0, 2, 3, 1).reshape(no_subjects, -1)

    # * compute subject-by-subject correlation matrix
    corr_matrix = np.corrcoef(X)

    # * extract upper triangle (excluding diagonal)
    upper = np.triu_indices(no_subjects, k=1)
    score = np.mean(corr_matrix[upper])

    return score


def get_accuracy(flips, flips_ref):
    """
    Computes the accuracy of the computed flips by comparing to the ground-truth.
    :param flips: A matrix containing 1's and 0's describing which channels the algorithm has suggested to flip for each subject.
    :param flips_ref: A matrix containing 1's and 0's containing the flips from the generative model/ground truth.
    :return: accuracy: A numeric accuracy value between min=0 and max=1.
    """
    no_subject = flips.shape[0]
    no_channel = flips.shape[1]

    ref_flip = np.copy(flips_ref)
    flips_ = np.copy(flips)

    ref_flip[ref_flip == 0] = -1
    flips_[flips_ == 0] = -1
    shape_acc = (int(no_subject * (no_subject -1)/2), int(no_channel * (no_channel-1)/2))
    accuracy_matrix = np.zeros(shape_acc)

    c1 = 0
    for sub_row1 in range(no_subject-1):
        for sub_row2 in range(sub_row1+1, no_subject):
            c2 = 0
            for chan_col1 in range(no_channel-1):
                for chan_col2 in range(chan_col1+1, no_channel):
                    s1 = ref_flip[sub_row1, chan_col1] * ref_flip[sub_row1, chan_col2] * ref_flip[sub_row2, chan_col1] * ref_flip[sub_row2, chan_col2]
                    s2 = flips_[sub_row1, chan_col1] * flips_[sub_row1, chan_col2] * flips_[sub_row2, chan_col1] * flips_[sub_row2, chan_col2]
                    if s1 == s2:
                        accuracy_matrix[c1,c2] = 1
                    c2 =  c2 + 1

            c1 = c1 + 1

    accuracy = np.mean(accuracy_matrix)
    return accuracy



def ctranspose(flips):
    """
    :param flips: numpy.ndarray, the 'flips' matrix
    :return:
    """
    temp = flips.transpose()
    return temp - 2j*temp.imag





