import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import scipy.io as sio
import scipy.signal as sig
from flip_data import flip_data

#~~~~~~~~~~ ORIGINAL UNAMBIGUOUS DATA ~~~~~~~~~~#
#load all subject files
directory_in_str = Path('0.5_sub_25_ch_10/')
matfiles = sorted(Path(directory_in_str).glob('**/*unflipped*.mat'))
df_dict = {}
df_large = pd.DataFrame()
sub = 0
for matfile in matfiles:
    mat_contents = sio.loadmat(matfile)
    s = mat_contents['X_MAR']

    df_mini = pd.DataFrame(s)
    df_large = df_large.append(df_mini)

    df_dict[sub] = df_mini  # * appends the original data for each subject to the dict
    sub = sub + 1

# ~~~~~~~~~~~~~~~~~~~ AMBIGUOUS DATA
# directory_in_str = Path('0.5_sub_25_ch_10/')
# matfiles = sorted(Path(directory_in_str).glob('**/*_ambiguous_data.mat'))
# df_dict = {}
# df_large = pd.DataFrame()
# sub = 0
# for matfile in matfiles:
#     mat_contents = sio.loadmat(matfile)
#     struct = mat_contents['S']
#     struct_fields = struct.dtype
#     struct_data = {n: struct[n][0, 0] for n in struct_fields.names}
#
#     df_mini = pd.DataFrame(struct_data['data'])
#     df_large = df_large.append(df_mini)
#
#     df_dict[sub] = df_mini  # * appends the original data for each subject to the dict
#     sub = sub + 1

# plot the coherence map for 3 channels
# specify 3 channel pairs to plot the coherence of
c1 = 5
c2 = 8
c3 = 9
fs = 250

# apply diego's flips
mat = sio.loadmat('dipole_signflip/src/dipole_signflip/diego.mat')  # read in flips from mat file
flips = mat['flips']
[diego_dict, df_diego] = flip_data(df_dict, len(df_dict[0]), flips, [], [])

#oxford code
mat = sio.loadmat('dipole_signflip/src/dipole_signflip/ox.mat')  # read in flips from mat file
flips = mat['flips']
[ox_dict, df_ox] = flip_data(df_dict, len(df_dict[0]), flips, [], [])

#ref flips
mat = sio.loadmat('dipole_signflip/src/dipole_signflip/ref.mat')  # read in flips from mat file
flips = mat['flips']
[ref_dict, df_ref] = flip_data(df_dict, len(df_dict[0]), flips, [], [])

# Create a figure with three subplots
fig, axs = plt.subplots(1, 3, figsize=(18/3, 6/3), dpi=300)
fig.subplots_adjust(wspace=1.8/3)
color1 = '#800080'
color2 = '#c3b1e1'
color3 = '#524f81'
color4 = '#9146ff'
for pair in range(3):
    if pair == 0:
            #ambg
            x = df_large.iloc[:,c1]
            y = df_large.iloc[:,c2]
            f, Cxy = sig.coherence(x, y, fs)
            axs[pair].semilogy(f, Cxy, label='Original', linewidth=4/3, linestyle='dashed', color=color1)
            axs[pair].set_xlabel('Frequency (Hz)', fontsize=16/3, weight='bold')
            axs[pair].set_ylabel('Coherence', fontsize=16/3, weight='bold')
            axs[pair].tick_params(axis='x', labelleft=True, labelsize=16/3)
            axs[pair].tick_params(axis='y', labelsize=16 / 3)

            #diego
            x = df_diego.iloc[:, c1]
            y = df_diego.iloc[:, c2]
            f, Cxy = sig.coherence(x, y, fs)
            axs[pair].semilogy(f, Cxy, label='Corrected', linewidth=4/3, color=color2)
            axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
            axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
            axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
            axs[pair].tick_params(axis='y', labelsize=16 / 3)

            # # oxford
            # x = df_ox.iloc[:, c1]
            # y = df_ox.iloc[:, c2]
            # f, Cxy = sig.coherence(x, y, fs)
            # axs[pair].semilogy(f, Cxy, label='Oxford', linewidth=4/3, color=color3)
            # axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
            # axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
            # axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
            # axs[pair].tick_params(axis='y', labelsize=16 / 3)

            # reference
            x = df_ref.iloc[:, c1]
            y = df_ref.iloc[:, c2]
            f, Cxy = sig.coherence(x, y, fs)
            axs[pair].semilogy(f, Cxy, label='Ground-Truth', linewidth=4/3, color=color4)
            axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
            axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
            axs[pair].tick_params(axis='x', labelleft=True, labelsize=16/3)
            axs[pair].tick_params(axis='y', labelsize=16/3)

            title = 'Coherence between channels X and Y'
            axs[pair].set_title(title, fontsize=16 / 3, color='black', weight='bold')



    elif pair == 1:
        # ambg
        x = df_large.iloc[:, c1]
        y = df_large.iloc[:, c3]
        f, Cxy = sig.coherence(x, y, fs)
        axs[pair].semilogy(f, Cxy, label='Original', linewidth=4 / 3, linestyle='dashed', color=color1)
        axs[pair].set_xlabel('Frequency (Hz)', fontsize=16 / 3, weight='bold')
        axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        axs[pair].tick_params(axis='y', labelsize=16 / 3)

        # diego
        x = df_diego.iloc[:, c1]
        y = df_diego.iloc[:, c3]
        f, Cxy = sig.coherence(x, y, fs)
        axs[pair].semilogy(f, Cxy, label='Corrected', linewidth=4 / 3, color=color2)
        axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
        axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        axs[pair].tick_params(axis='y', labelsize=16 / 3)

        # # oxford
        # x = df_ox.iloc[:, c1]
        # y = df_ox.iloc[:, c3]
        # f, Cxy = sig.coherence(x, y, fs)
        # axs[pair].semilogy(f, Cxy, label='Oxford', linewidth=4 / 3, color=color3)
        # axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
        # axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        # axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        # axs[pair].tick_params(axis='y', labelsize=16 / 3)

        # reference
        x = df_ref.iloc[:, c1]
        y = df_ref.iloc[:, c3]
        f, Cxy = sig.coherence(x, y, fs)
        axs[pair].semilogy(f, Cxy, label='Ground-Truth', linewidth=4 / 3, color=color4)
        axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
        axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        axs[pair].tick_params(axis='y', labelsize=16 / 3)

        title = 'Coherence between channels X and Z'
        axs[pair].set_title(title, fontsize=16 / 3, color='black', weight='bold')

    else:
        # ambg
        x = df_large.iloc[:, c2]
        y = df_large.iloc[:, c3]
        f, Cxy = sig.coherence(x, y, fs)
        axs[pair].semilogy(f, Cxy, label='Original', linewidth=4 / 3, linestyle='dashed', color=color1)
        axs[pair].set_xlabel('Frequency (Hz)', fontsize=16 / 3, weight='bold')
        axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        axs[pair].tick_params(axis='y', labelsize=16 / 3)

        # diego
        x = df_diego.iloc[:, c2]
        y = df_diego.iloc[:, c3]
        f, Cxy = sig.coherence(x, y, fs)
        axs[pair].semilogy(f, Cxy, label='Corrected', linewidth=4 / 3, color=color2)
        axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
        axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        axs[pair].tick_params(axis='y', labelsize=16 / 3)

        # # oxford
        # x = df_ox.iloc[:, c2]
        # y = df_ox.iloc[:, c3]
        # f, Cxy = sig.coherence(x, y, fs)
        # axs[pair].semilogy(f, Cxy, label='Oxford', linewidth=4 / 3, color=color3)
        # axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
        # axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        # axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        # axs[pair].tick_params(axis='y', labelsize=16 / 3)

        # reference
        x = df_ref.iloc[:, c2]
        y = df_ref.iloc[:, c3]
        f, Cxy = sig.coherence(x, y, fs)
        axs[pair].semilogy(f, Cxy, label='Ground-Truth', linewidth=4 / 3, color=color4)
        axs[pair].set_xlabel('Frequency (Hz)', fontsize=14 / 3, weight='bold')
        axs[pair].set_ylabel('Coherence', fontsize=16 / 3, weight='bold')
        axs[pair].tick_params(axis='x', labelleft=True, labelsize=16 / 3)
        axs[pair].tick_params(axis='y', labelsize=16 / 3)

        title = 'Coherence between channels Y and Z'
        axs[pair].set_title(title, fontsize=16 / 3, color='black', weight='bold')
        axs[pair].legend(prop={'size': 15 / 3}, loc='upper right')


    plt.show()


