#!/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from sklearn import svm
from scipy import stats


def cpNormal(x, mean, sigma2):
    X = np.double(x)
    Mean = np.double(mean)
    Sigma2 = np.double(sigma2)

    cp1 = 1.0 / ((2.0 * np.pi) ** 0.5)
    cp2 = (-1.0 / 2.0) * ((X - Mean) ** 2.0 / Sigma2)
    CP = cp1 * np.e ** cp2

    return CP

def cpNormal2(x, mean, sigma2):
    X = stats.norm(loc = np.float64(mean), scale = np.float64(sigma2) ** 0.5)
    y = X.pdf(np.float64(x))

    return y


if __name__ == "__main__":
    print cpNormal(0, 0 , 1)
    print cpNormal2(0, 0 , 1)
