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
    #得到所有采样区域
    value = src_db.query_calibration("select distinct calibration_value \
                                      from calibration_original")
    for v in value:
        #得到一个区域采集的时间点
        time_id = src_db.query_calibration("select distinct calibration_timestamp_id \
                                            from calibration_original \
                                            where calibration_value = %d" % v)
        #得到一个区域一次采集到的AP物理地址
        ap_all_list = []
        for t in time_id:
            bssid = src_db.query_calibration("select bssid \
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
            s = src_db.query_calibration("select signal_strength \
                                         from calibration_original \
                                         where calibration_value = %d and bssid = \'%s\'" % (v, ap))

            signal_src_array = np.array(s, dtype = np.float64)
            signal_array = np.array(s, dtype = np.float64)

            #将信号指数计算成物理信号值
            i = 0
            for s_t in signal_array:
                signal_array[i] = 10 ** (s_t / 10)
                i = i + 1
                
            #计算出一个AP的平均物理信号值 再还原为该AP的平均信号指数
            signal_mean = 10 * np.log10(signal_array.mean())

            #根据AP的平均信号指数计算出AP的信号方差
            sigma = np.float64(0.0)
            for j in s:
                sigma = sigma + np.float64((j - signal_mean) ** 2.0)

            #将AP的信号平均指数和方差保存为列表
            signal_mean_list.append(signal_mean)
            sigma_list.append(sigma / np.float64(len(signal_src_array) - 1))

        print "value :", v, "ap_training_list len :", len(ap_training_list)
        print "signal mean:", signal_mean_list
        print "sigma :", sigma_list

        #将校准数据存入数据库
        

def calibration_core():
    pass

if __name__ == "__main__":
    src_db = Mysql()
    src_db.open_session()
    calibration_training()
    calibration_core()
    src_db.close_session()

