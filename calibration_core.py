#!/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import *
from sqlalchemy.schema import ForeignKey
from sqlalchemy import distinct

import numpy as np
from scipy import stats
from sklearn import svm

import datetime
import time

DB_CONNECT_STRING = "mysql+pymysql://root:qwer#1234@127.0.0.1/wifi_tracing"
BaseModel = declarative_base()

class Mysql:

    def __init__(self):
        self.engine = create_engine(DB_CONNECT_STRING, echo=False)
        self.DBSession = sessionmaker(bind=self.engine)
        self.session = None
        pass

    def init_db(self):
        BaseModel.metadata.create_all(self.engine)

    def drop_db(self):
        BaseModel.metadata.drop_all(self.engine)

    def open_session(self):
        self.session = self.DBSession()

    def close_session(self):
        if self.session:
            self.session.close()
            self.session = None

    def insert_calibration(self, d):
        assert(self.session)
        ts = d["timestamp"]
        q = self.session.query(CalibrationTimestamp)
        qo = q.filter(CalibrationTimestamp.timestamp == ts).scalar()
        if not qo:
            qo = CalibrationTimestamp(ts)
            self.session.add(qo)
            self.session.commit()

        assert(qo)
        ts_id = qo.id
        
        co = CalibrationOriginal(d["ssid"], d["bssid"], d["signal_strength"],
                                 d["calibration_value"], ts_id)
        self.session.add(co)
        self.session.commit()

    def clear_calibration(self, sql):
        self.session.execute(sql)

    def create_table(self, sql):
        self.session.execute(sql)

    def insert_calibration(self, sql):
        self.session.execute(sql)

    def query_calibration(self, sql):
        q = self.session.execute(sql)

        ret = []
        for line in q:
            ret.append(line[0])

        return ret

    def query_calibration2(self, sql):
        q = self.session.execute(sql)

        ret = []
        for line in q:
            ret.append([line[0], line[1]])

        return ret

    def query_calibration3(self, sql):
        q = self.session.execute(sql)

        ret = []
        for line in q:
            ret.append([line[0], line[1], line[2]])

        return ret

    def query_calibration4(self, sql):
        q = self.session.execute(sql)

        ret = []
        for line in q:
            ret.append([line[0], line[1], line[2], line[3]])

        return ret
        
#------------------------------------------------------------------------------
        
class CalibrationOriginal(BaseModel):
    __tablename__ = 'calibration_original'

    id = Column('id', Integer, primary_key=True)
    ssid = Column("ssid", String(256))
    bssid = Column("bssid", String(256))
    signal_strength = Column("signal_strength", Integer)
    calibration_value = Column("calibration_value", Integer)
    calibration_timestamp_id = Column("calibration_timestamp_id", 
                                      Integer, 
                                      ForeignKey("calibration_timestamp.id"),
                                      nullable=False)
    def __init__(self, ssid, bssid, signal_strength, 
                 calibration_value, calibration_timestamp_id):
        self.id = None
        self.ssid = ssid
        self.bssid = bssid
        self.signal_strength = signal_strength
        self.calibration_value = calibration_value
        self.calibration_timestamp_id = calibration_timestamp_id

    def __repr__(self):
        d = {}
        d['id'] = self.id
        d["ssid"] = self.ssid
        d["bssid"] = self.bssid
        d["signal_strength"] = self.signal_strength
        d["calibration_value"] = self.calibration_value
        d["calibration_timestamp_id"] = self.calibration_timestamp_id
        return str(d)

########################################################################

def calibration_training():
    db.clear_calibration("delete from calibration_training")

    #得到所有采样区域
    value = db.query_calibration("select distinct calibration_value \
                                      from calibration_original")
    for v in value:
        #得到一个区域采集的时间点
        time_id = db.query_calibration("select distinct calibration_timestamp_id \
                                            from calibration_original \
                                            where calibration_value = %d" % v)
        #得到一个区域一次采集到的AP物理地址
        ap_all_list = []
        for t in time_id:
            bssid = db.query_calibration("select bssid \
                                              from calibration_original \
                                              where calibration_value = %d and calibration_timestamp_id = %d" % (v, t))
            ap_all_list.extend(bssid)

        #从一个区域一次手机到的AP中选出出现频率大于90%的AP
        ap_training_list = []
        for ap in ap_all_list:
            if ap_all_list.count(ap) >= len(time_id) * 0.9:
                if ap_training_list.count(ap) == 0:
                    ap_training_list.append(ap)

        signal_mean_list = []
        sigma_list = []
        for ap in ap_training_list:
            #根据区域和选出的有效AP 得到该AP的所有信号指数
            s = db.query_calibration("select signal_strength \
                                         from calibration_original \
                                         where calibration_value = %d and bssid = \'%s\'" % (v, ap))

            signal_src_array = np.array(s, dtype = np.float64)
            signal_array = np.array(s, dtype = np.float64)

            #将信号指数计算成物理信号值
            i = 0
            for s_t in signal_array:
                signal_array[i] = np.float64(10.0 ** (s_t / 10.0))
                i = i + 1
                
            #计算出一个AP的平均物理信号值 再还原为该AP的平均信号指数
            signal_mean = np.float64(10 * np.log10(signal_array.mean()))

            #根据AP的平均信号指数计算出AP的信号方差
            sigma = np.float64(0.0)
            for j in s:
                sigma = sigma + np.float64((j - signal_mean) ** 2.0)

            sigma = sigma / np.float64(len(signal_src_array) - 1)

            #将AP的信号平均指数和方差保存为列表
            #signal_mean_list.appden(signal_mean)
            #sigma_list.append(sigma)

            #将校准数据存入数据库
            print "Insert : ", v, ap, signal_mean, sigma
            db.insert_calibration("insert into calibration_training \
                                   values (0, %s, \'%s\', %s, %s)" % (v, ap, signal_mean, sigma))


def calibration_training2():
    #db.create_table("create table new_training (value bigint, ap_ref char(255), ap_d double, bssid char(255), mean double, sigma double)")

    db.insert_calibration("delete from new_training")

    #得到所有采样区域
    value = db.query_calibration("select distinct calibration_value \
                                      from calibration_original")

    training_ap_list = []
    for v in value:
        #得到一个区域采集的时间点
        time_id = db.query_calibration("select distinct calibration_timestamp_id \
                                            from calibration_original \
                                            where calibration_value = %d" % v)

        #得到一个区域一次采集到的AP物理地址
        ap_max_list = []
        for t in time_id:
            bssid = db.query_calibration("select bssid \
                                              from calibration_original \
                                              where calibration_value = %d and calibration_timestamp_id = %d \
                                              order by signal_strength desc" % (v, t))
            ap_max_list.append(bssid[0])

        #得到该区域信号最强的AP 作为基准AP
        for ap in ap_max_list:
            if ap_max_list.count(ap) > (len(ap_max_list) / 2):
                ap_ref = ap
                break

        #得到一个区域一次采集到的AP物理地址
        ap_all_list = db.query_calibration("select distinct bssid \
                                              from calibration_original \
                                              where calibration_value = %d" % v)

        training_ap_list_t =[]
        for ap in ap_all_list:
            #根据区域和选出的AP 得到该AP的所有信号指数
            s = db.query_calibration("select signal_strength \
                                         from calibration_original \
                                         where calibration_value = %d and bssid = \'%s\'" % (v, ap))

            if len(s) <= 1: continue

            signal_src_array = np.array(s, dtype = np.float64)
            signal_array = np.array(s, dtype = np.float64)

            #将信号指数计算成物理信号值
            i = 0
            for s_t in signal_array:
                signal_array[i] = np.float64(10.0 ** (s_t / 10.0))
                i = i + 1
                
            #计算出一个AP的平均物理信号值 再还原为该AP的平均信号指数
            signal_mean = np.float64(10 * np.log10(signal_array.mean()))

            sigma = np.float64(0.0)
            for j in signal_src_array:
                sigma = sigma + np.float64((j - signal_mean) ** 2.0)

            sigma = sigma / np.float64(len(signal_src_array) - 1)
            if sigma == 0.0 : continue

            training_ap_list_t.append([ap, signal_mean, sigma])

        
        for i in training_ap_list_t:
            if i[0] == ap_ref:
                ap_ref_v = i[1]

        for i in training_ap_list_t:
            ap_d = i[1] - ap_ref_v
            training_ap_list.append([v, ap_ref, ap_d, i[0], i[1], i[2]])

    for i in training_ap_list:
        db.insert_calibration("insert into new_training \
                               values (%s, \'%s\', %s, \'%s\', %s, %s)" % (i[0], i[1], i[2], i[3], i[4], i[5]))
        #print i

def gaussian_cp(x, xmean, sigma):
    X = stats.norm(loc = np.float64(xmean), scale = np.float64(sigma))
    Y = X.pdf(np.float64(x))

    return Y


def d_normal(lp_list, index, cp_list):
    ref_v = lp_list[index][1]

    ap_list = []
    i = 0
    for ap in lp_list:
        ap_list.append([ap[0], (ap[1] - ref_v)])

    cp = np.float64(0.0)
    for ap in ap_list:
        for ap_t in cp_list:
            if ap[0] == ap_t[1]:
                cp = cp + gaussian_cp(ap[1], ap_t[2], ap_t[3])
                
    return cp


def calibration_normal2(ap_list):
    ret = None
    ret_v = -1

    value =  db.query_calibration("select distinct value \
                                      from new_training")

    for v in value:
        training_ap_list = db.query_calibration4("select ap_ref, bssid, ap_d, sigma \
                                                 from new_training \
                                                 where value = %s" % v)

        i = 0
        ref_v = training_ap_list[0][0]
        for ap in ap_list:
            if ap[0] == ref_v:
                t = np.float64(d_normal(ap_list, i, training_ap_list))
                if ret_v < t:
                    ret_v = t
                    ret = v
                    break
                else:
                    continue
                    
            i = i + 1
            
    return ret


def calibration_normal(ap_list):
    value =  db.query_calibration("select distinct calibration_value \
                                      from calibration_training")

    cp_list = []
    for v in value:
        training_ap_list = db.query_calibration3("select bssid, calibration_ap_value_mean, sigma \
                                                 from calibration_training \
                                                 where calibration_value = %s" % v)

        cp = np.float64(0.0)
        for ap in ap_list:
            for ap_t in training_ap_list:
                if ap[0] == ap_t[0]:
                    cp = cp + gaussian_cp(ap[1], ap_t[1], ap_t[2])

        cp_list.append([cp, v])

    cp_list.sort()

    if cp_list[-1][0] == 0.0 or ((cp_list[-1][0] - cp_list[-2][0]) / cp_list[-1][0]) < 0.1:
        cp_value = -1
    else:
        cp_value = cp_list[-1][1]

    return cp_value

def calibration_core():
    #得到所有待测区域
    value = db.query_calibration("select distinct calibration_value \
                                      from calibration_original")
    for v in value:
        #得到一个待测区域采集的时间点
        time_id = db.query_calibration("select distinct calibration_timestamp_id \
                                            from calibration_original \
                                            where calibration_value = %d" % v)
        #得到一个待测区域一次采集到的AP物理地址
        for t in time_id:
            bssid = db.query_calibration("select bssid, signal_strength \
                                              from calibration_original \
                                              where calibration_value = %d and calibration_timestamp_id = %d" % (v, t))

            ap_list = []
            for ap in bssid:
                ap_list.extend(db.query_calibration2("select bssid, signal_strength \
                                              from calibration_original \
                                              where calibration_value = %s and calibration_timestamp_id = %s and bssid = \'%s\'" % (v, t, ap)))

            #print v, t, ap_list
            #ret = calibration_normal(ap_list)
            ret = calibration_normal2(ap_list)
            if ret == None:
                print "This value ", v, " time ", t, " can not calibration!"
            else:
                print "Src : ", v, t, " <==========> ", "CP return : ", ret
                
        print ""

if __name__ == "__main__":
    db = Mysql()
    db.open_session()
    #calibration_training()
    calibration_training2()
    calibration_core()
    db.close_session()

