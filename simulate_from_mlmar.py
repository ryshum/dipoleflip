import numpy as np


def sim_mlmar(W, T_new, X_init):
    if (type(T_new)) is int:
        N_new = 1
        T_new = [T_new]
    else:
        N_new = T_new.shape[0]
    channels = W.shape[1]  # no. of channels
    order = W.shape[0]/channels
    orders = np.arange(1, order+1)

    if X_init is None:
        d = 500
    else:
        d = X_init.shape[0]

    for n in range(N_new):
        if X_init is not None:
            shape = [d+T_new[n], channels]
            Xin = np.zeros(shape)
            Xin[0:d, :] = X_init
            Xin[d+1:, :] = np.random.randn([T_new[n], channels]) * np.matlib.repmat(np.std(X_init), T_new[n], 1)
        else:
            Xin = np.random.randn(d+T_new[n], channels)

        for t in range(int(order), T_new[n]+d):
            XX = np.ones([1, int(order)*channels])
            for i in range(len(orders)):
                o = int(orders[i])
                XX[0, 0+i*channels : channels+i*channels] = Xin[t-o, :]

            Xin[t, :] = Xin[t, :] + np.matmul(XX, W)

        ind = np.arange(0, T_new[n], dtype='int') + int(np.sum(T_new[1:n-1]))
        X = np.empty((len(ind), channels))
        X[ind, :] = Xin[d:, :]

        return X

