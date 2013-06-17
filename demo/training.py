#!/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import db

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
                     signal_strength > %s"
        bssid_number4vt = int(src_db.execute_sql_ret1(sql % (number4v, bv, -100))[0])
        if bssid_number4vt < times_number4v - 2:
            continue
            
        sql = "select signal_strength \
               from calibration_original \
               where calibration_value = %s and \
                     bssid = \'%s\' and \
                     signal_strength > %s \
               order by signal_strength desc"
        signal_list = src_db.execute_sql_ret1(sql % (number4v, bv, -100))
        signal_array = np.array(signal_list, dtype = np.float64)

        i = 0
        for s in signal_array:
            signal_array[i] = 10.0 ** (np.float64(s) / 10.0)
            i = i + 1
            
        signal_mean = 10 * np.log10(signal_array.sum() / len(signal_array))

        sigma = np.float64(0.0)
        for s in signal_list:
            sigma = sigma + (s - signal_mean) ** 2.0
            
        sigma = sigma / len(signal_list)
        
        finish_list.append([signal_mean, bv, sigma])

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
        ref = finish_list[0][0]

        i = 0
        for line in finish_list:
            finish_list[i][0] = line[0] - ref
            i = i + 1

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
    
