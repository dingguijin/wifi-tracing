#!/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import db
import example
import normal
import svm

def print_ret(ret):
    for r in ret:
        print r

    print "len : ", len(ret)


def normal_cp(onetime_aplist, training_list):
    cp = np.float64(0.0)
    for ap in onetime_aplist:
        for tr in training_list:
            if ap[1] == tr[0]:
                B = np.float64(tr[2]) ** 2.0
                C = np.float64((2 * np.pi) ** 0.5)
                mRSS = np.float64(tr[1])
                RSS = np.float64(ap[2])
                cp = cp + normal.cpNormal(RSS, mRSS, B)

    return cp * 100


def do_calibration(src_db, onetime_aplist):
    sql = "select distinct value from training"
    value_list = src_db.execute_sql_ret1(sql)
    onetime = []
    onetime.extend(onetime_aplist)

    CP_list = []
    for nv in value_list:
        sql = "select bssid, signal_d, sigma \
               from training \
               where value = %s"
        training_list = src_db.execute_sql_ret3(sql % nv)

        cp = normal_cp(onetime, training_list)
        CP_list.append([cp, nv])

    if len(CP_list) < 2: return None

    CP_list.sort()
    CP_list.reverse()

    #print_ret(CP_list)

    return [CP_list[0][1], CP_list[1][1]]


def do_svm(src_db, value_list, cp_list):
    sql = "select bssid, signal_d from training where value = %s"

    LP = []
    for v in value_list:
        lp = src_db.execute_sql_ret2(sql % v)
        LP.append(lp)

    CP_list = []
    LP_list0 = []
    LP_list1 = []
    for cp in cp_list:
        for lp0 in LP[0]:
            if cp[1] == lp0[0]:
                for lp1 in LP[1]:
                    if cp[1] == lp1[0]:
                        CP_list.append(cp[2])
                        LP_list0.append(lp0[1])
                        LP_list1.append(lp1[1])
                    else:
                        continue

            else:
                continue


    if len(CP_list) < 4: return None

    ret = svm.cpSvm(CP_list, LP_list0, value_list[0], LP_list1, value_list[1])

    return ret

def realCalibration(CP):
    src_db = db.Mysql()
    src_db.open_session()

    normalValue = do_calibration(src_db, CP)
    print "Normal Calibration Value ---> : ", normalValue 

    if normalValue != None:
        svmValue = do_svm(src_db, normalValue, CP)
        print "Svm Calibration Value ===> : ", svmValue

    src_db.close_session()


if __name__ == "__main__":
    src_db = db.Mysql()
    src_db.open_session()

    ap4vt_list = example.get_example_ap(src_db)
    for onetime_aplist in ap4vt_list:
        #calibration_value = do_calibration(src_db, onetime_aplist)
        #print "Src value : ", onetime_aplist[0][0], " <=========> ", "Calibration value : ", calibration_value 
        print "Src value : ", onetime_aplist[0][0] 
	realCalibration(onetime_aplist)

    src_db.close_session()


