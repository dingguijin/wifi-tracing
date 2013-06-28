#!/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from sklearn import svm
from scipy import stats


def cpSvm(x, lp0, v0, lp1, v1):
    cp_mean_array0 = np.array(lp0, dtype=np.float64)
    cp_mean_array1 = np.array(lp1, dtype=np.float64)
    cp_mean_array = np.array([cp_mean_array0, cp_mean_array1])
    svc = svm.SVC(kernel='rbf')
    svc.fit(cp_mean_array, [np.float64(v0), np.float64(v1)])

    ret = svc.predict(np.array(x, dtype=np.float64))

    return ret
    

if __name__ == "__main__":
    print cpSvm([2,4,6,8,8,10], [1,3,5,6,7,9], 0, [12,14,23,24,29,35], 1)
