#!/bin/env python
# -*- coding: utf-8 -*-

import db
import numpy as np

def print_ret(ret):
    for r in ret:
        print r

    print "len : ", len(ret)

def get_example_ap(src_db):
    sql = "select distinct calibration_value \
           from calibration_original"
    number4v = src_db.execute_sql_ret1(sql)

    ap_list = []
    for nv in number4v:
        sql = "select distinct calibration_timestamp_id \
               from calibration_original \
               where calibration_value = %s"
        timesid4v_list = src_db.execute_sql_ret1(sql % nv)

        for tv in timesid4v_list:
            sql = "select calibration_value, bssid, signal_strength \
                   from calibration_original \
                   where calibration_value = %s and \
                   calibration_timestamp_id = %s"
            ap_tmp = src_db.execute_sql_ret3(sql % (nv, tv))

            ap_list.append(ap_tmp)

    return ap_list

if __name__ == "__main__":
    src_db = db.Mysql()
    src_db.open_session()
    print_ret(get_example_ap(src_db))
    src_db.close_session()
