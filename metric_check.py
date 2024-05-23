from scipy.signal import lfilter, hilbert, butter
import numpy as np
from pathlib import Path
import scipy.io
import pandas as pd


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def instantaneous_phase_method(directory):
        # read files in the folder for all subjects
        directory_in_str = Path(directory)
        matfiles = sorted(Path(directory_in_str).glob('**/*_ambiguous_data.mat'))

        average_phase_df = pd.DataFrame()
        for matfile in matfiles:  # loop over patients
            path_in_str = str(matfile)
            mat = scipy.io.loadmat(path_in_str)

            struct = mat['S']  # specify the struct in the .mat file that holds all data and info
            struct_fields = struct.dtype  # get names of the fields in the struct

            # * for convenience make dictionary using field names
            struct_data = {n: struct[n][0, 0] for n in struct_fields.names}

            # * specify the data field and get data from the struct and arrange in dataframe
            df = pd.DataFrame(struct_data['data'])

            # * determine the no. of channels & trials
            channels = df.shape[1]
            timepoints = df.shape[0]

            instant_phase_df = pd.DataFrame()
            for chan in range (0, channels):
                # 1. use a bandpass filter to remove the alpha freqs [8 , 12 Hz]
                # set sampling rate and desired frequency cut-offs
                data = 0
                fs = 250
                lowcut = 8
                highcut = 12
                y = butter_bandpass_filter(df[chan], lowcut, highcut, fs)

                # 2. extract the analytic signal
                analytic_y = hilbert(y)
                amp_envelope = np.abs(analytic_y)
                inst_phase = np.unwrap(np.angle(analytic_y))
                inst_freq  = (np.diff(inst_phase) / (2.0*np.pi)*fs)

                # save these values for instantaneous phase to average over them later on
                instant_phase_df['channel ' + str(chan)] = pd.Series(inst_phase)

            # average over all channels & save for each subject
            mean = instant_phase_df.mean(axis=0)
            average_phase_df._append(mean)

        # sum across subjects
        sum = average_phase_df.sum(axis=0)

        # average across time
        time_average = sum.mean()


