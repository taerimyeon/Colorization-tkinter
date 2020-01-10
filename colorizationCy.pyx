# -*- coding: utf-8 -*-
"""
Created on Sun Dec 22 21:57:48 2019

@author: Steven Jonathan (github: tttdddstvn)
"""


import cv2
import math
import time
import cython
import numpy as np
import scipy.sparse as spr
import matplotlib.pyplot as plt
from scikits.umfpack import spsolve
from time import perf_counter as perf


def rgb2ntsc(A):
    ' Convert RGB to YIQ '
    YIQ = np.zeros_like(A)
    YIQ[:, :, 0] = 0.299 * A[:,:,0] + 0.587 * A[:,:,1] + 0.114 * A[:,:,2]
    YIQ[:, :, 1] = 0.596 * A[:,:,0] - 0.275 * A[:,:,1] - 0.321 * A[:,:,2]
    YIQ[:, :, 2] = 0.212 * A[:,:,0] - 0.523 * A[:,:,1] + 0.311 * A[:,:,2]
    return YIQ


def ntsc2rgb(A):
    ' Convert YIQ to RGB '
    RGB = np.zeros_like(A)
    RGB[:, :, 0] = 1.000 * A[:,:,0] + 0.956 * A[:,:,1] + 0.621 * A[:,:,2]
    RGB[:, :, 1] = 1.000 * A[:,:,0] - 0.272 * A[:,:,1] - 0.647 * A[:,:,2]
    RGB[:, :, 2] = 1.000 * A[:,:,0] - 1.106 * A[:,:,1] + 1.703 * A[:,:,2]
    RGB = np.where(RGB > 0, RGB, 0)
    RGB = np.where(RGB <= 1., RGB, 1)
    return RGB


def colorize(colorIm, ntscIm):
    nI = np.zeros_like(ntscIm)
    nI[:, :, 0] = ntscIm[:, :, 0]  # Copy 'Y' channel to nI[:,:,0]
    cdef int m = ntscIm.shape[0]
    cdef int n = ntscIm.shape[1]
    img_size = m * n
    img_mat = np.arange(img_size)
    lbl_idxs = img_mat.reshape(m, n)[np.where(colorIm)]  # Store marked pixel indices
    lbl_idxs.sort()
    img_mat = img_mat.reshape(m, n)
    
    cdef int i, j, ii, jj, it  # For iterator
    cdef int tlen = 0
    cdef int wd = 1  # Width of window
    cdef int length = 0  # Total length
    cdef int consts_len = 0  # For row indices counter
    cdef double startTime  # Start time ticker
    cdef double endTime  # End time ticker
    # All cols_inds, row_inds, vals, and gvals are 1-D array
    col_inds = np.zeros(img_size * (2*wd+1)**2)  # img_size*9 because 3x3 window
    row_inds = np.zeros(img_size * (2*wd+1)**2)
    vals = np.zeros(img_size * (2*wd+1)**2)
    gvals = np.zeros(img_size * (2*wd+1)**2)
    # Define memory view for efficient memory access in for loop
    cdef double[:] weight = vals
    cdef double[:] memgvals = gvals
    cdef double[:] colIdx = col_inds
    cdef double[:] rowIdx = row_inds
    cdef long[:, :] memimgmat = img_mat
    cdef double[:, :] memntsc = ntscIm[:, :, 0]
    cdef double tmpArr[9]  # To contain temporary pixel in a 3*3 window
    cdef double[:] memtmpArr = tmpArr
    
    print("Creating weight matrix...")
    startTime = perf()
    '''Start ticker'''
    for i in range(m):
        for j in range(n):
            if not colorIm[i, j]:  # colorIm = difference image (Boolean)
                tlen = 0
                # Apply windowing/find neighbourhood (max 3*3)
                for ii in range(max(0,i-wd), min(i+wd+1,m)):
                    for jj in range(max(0,j-wd), min(j+wd+1,n)):
                        if (ii != i) or (jj != j):
                            memgvals[tlen] = memntsc[ii, jj]
                            # consts_len is only incremented when j increases
                            rowIdx[length] = consts_len
                            colIdx[length] = memimgmat[ii, jj]
                            tlen += 1
                            length += 1
                t_val = memntsc[i, j]  # Chosen pixel
                memgvals[tlen] = t_val  # tlen should be N(r) + 1
                M = len(memgvals[0:tlen+1])  # Number of pixels in a window
                temp = 0
                for it in range(M):
                    temp += memgvals[0:tlen+1][it]
                Mean = float(temp)/M  # Mean in a window
                temp = 0  # Reset for next operation
                for it in range(M):
                    temp += (memgvals[0:tlen+1][it]-Mean)**2  # Squared diff
                cvar = float(temp)/M  # Calculate variance
                temp = 0
                csig = cvar * 0.6
                # Calculate minimum square distance of pixel r neighbour
                tmp = []
                for it in range(M-1):
                    tmp.append((memgvals[0:tlen][it]-t_val)**2)
                mgv = min(tmp)
                if csig < (-mgv/math.log(0.01)):
                    csig = -mgv/math.log(0.01)
                if csig < 2e-6:
                    csig = 2e-6
                # Calculate weight_rs for neighbour of pixel r
                for it in range(M-1):
                    tmpArr[it] = math.exp(-1*(memgvals[0:tlen][it]-t_val)**2/csig)
                    temp += tmpArr[it]
                for it in range(M-1):
                    tmpArr[it] = -1*(tmpArr[it]/temp)
                temp = 0
                weight[length-tlen:length] = memtmpArr[0:tlen]
            rowIdx[length] = consts_len
            colIdx[length] = memimgmat[i, j]
            weight[length] = 1  # Value for diagonal, i == j == 1
            length += 1
            consts_len = consts_len + 1
    '''End ticker'''
    endTime = perf()
    print("Weight matrix creation done in:"+
          " {0:.3f} second(s)".format(endTime-startTime))
    weight = weight[0:length]  # We don't need the rest, so slice until length
    rowIdx = rowIdx[0:length]
    colIdx = colIdx[0:length]
    
    print("Solving sparse matrix...")
    startTime = perf()
    A = spr.coo_matrix((weight, (rowIdx, colIdx)),
                       shape=(consts_len, img_size)).tocsr()
    b = np.zeros(A.shape[0])
    
    for t in range(1, 3):  # Only solve for U and V channel
        b[lbl_idxs] = ntscIm[:, :, t].reshape(img_size)[lbl_idxs]
        new_vals = spsolve(A,  b)
        nI[:, :, t] = new_vals.reshape(m, n)
    endTime = perf()
    print("Solving sparse matrix done in:"+
          " {0:.3f} second(s)".format(endTime-startTime))
    
    return nI
