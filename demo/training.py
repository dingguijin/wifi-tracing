#!/bin/env python
# -*- coding: utf-8 -*-

import db
import numpy as np

def print_ret(ret):
    for t in ret:
        print t
        
    print "len : ", len(ret)

def lookup_onevalue(number4v, bssid4v, times_number4v):
    finish_list = []
    for bv in bssid4v:
        #获取一个区域内一个AP的出现次数
        sql = "select count(bssid) \
               from calibration_original \
               where calibration_value = %s and \
                     bssid = \'%s\' and \
                     signal_strength >= %s"
        bssid_number4vt = int(src_db.execute_sql_ret1(sql % (number4v, bv, -99))[0])
        #if bssid_number4vt < times_number4v * 0.9:
        if bssid_number4vt < 4 :
            continue
            
        sql = "select signal_strength \
               from calibration_original \
               where calibration_value = %s and \
                     bssid = \'%s\' and \
                     signal_strength >= %s \
               order by signal_strength desc"
        signal_list = src_db.execute_sql_ret1(sql % (number4v, bv, -100))

        sum = np.double(0.0)
        for s in signal_list:
            sum = sum + 10.0 ** (np.float64(s) / 10.0)

        signal_mean = sum / len(signal_list)
        signal_mean = 10 * np.log10(signal_mean)

        sigma2sum = np.double(0.0)
        for s in signal_list:
            sigma2sum = sigma2sum + (s - signal_mean) ** 2.0

        sigma2 = sigma2sum / (len(signal_list) - 1)
        if sigma2 == 0: continue

        finish_list.append([signal_mean, bv, sigma2])

    return finish_list

def make_src_db(src_db, number4v):
    for nv in number4v:
        #获取一个区域内出现过的AP
        sql = "select distinct bssid \
               from calibration_original \
               where calibration_value = %s and \
                     signal_strength > %s"
        bssid4v = src_db.execute_sql_ret1(sql % (nv, -100))

        #获取一个区域内的采样次数
        sql = "select count(distinct calibration_timestamp_id) \
               from calibration_original \
               where calibration_value = %s"
        times_number4v = int(src_db.execute_sql_ret1(sql % nv)[0])
        finish_list = lookup_onevalue(nv, bssid4v, times_number4v)
        finish_list.sort()
        finish_list.reverse()

        sql = "insert training values (%s, \'%s\', %s, %s)"
        for line in finish_list:
            src_db.execute_sql_ret0(sql % (nv, line[1], line[0], line[2]))

def build_training_table(src_db):
    sql = "select distinct calibration_value from calibration_original"
    value_number = src_db.execute_sql_ret1(sql)
    sql = "delete from training"
    src_db.execute_sql_ret0(sql)
    make_src_db(src_db, value_number)

if __name__ == "__main__":
    src_db = db.Mysql()
    src_db.open_session()
    build_training_table(src_db)
    src_db.open_session()
    
