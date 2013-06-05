# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
#from sqlalchemy.types import CHAR, Integer, String, DateTime, Numeric, Float
from sqlalchemy.types import *
from sqlalchemy.schema import ForeignKey
from sqlalchemy import distinct

import numpy as np
from scipy import stats

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
        #ts = datetime.datetime.fromtimestamp(d["timestamp"])
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


    def insert_calibration_training(self, d):
        co = CalibrationTraining(d["calibration_value"],
                                 d["bssid"],
                                 d["ap_value_mean"],
                                 d["sigma"])
                                 #d["cp_value"])
        self.session.add(co)
        self.session.commit()

    def clear_calibration_training(self):
        self.session.query(CalibrationTraining).delete()
        self.session.commit()


    #select all value from calibration.
    def query_calibration_value(self):
        q = self.session.query(distinct(CalibrationOriginal.calibration_value))

        value_list = []
        for v in q:
            value_list.append(v[0])

        return value_list
        
    def query_calibration_by_value(self, value):
        q = self.session.query(distinct(CalibrationOriginal.calibration_timestamp_id)).filter(CalibrationOriginal.calibration_value == value)

        timestamp_list = []
        for t in q:
            timestamp_list.append(t[0])

        return timestamp_list

    def query_calibration_by_value_timestamp(self, value, timestamp):
        q = self.session.query(CalibrationOriginal.bssid, CalibrationOriginal.signal_strength).filter(CalibrationOriginal.calibration_value == value, CalibrationOriginal.calibration_timestamp_id == timestamp, CalibrationOriginal.signal_strength <= -30, CalibrationOriginal.signal_strength >= -100)

        ap_list = []
        for ap in q:
            #ap_list.append([ap[0], ap[1]])
            ap_list.append(ap[0])

        return ap_list

    def query_calibration_by_value_bssid(self, value, bssid):
        q = self.session.query(CalibrationOriginal.signal_strength).filter(CalibrationOriginal.calibration_value == value, CalibrationOriginal.bssid == bssid)

        ap_value_list = []
        for ap in q:
            ap_value_list.append(ap[0])

        return ap_value_list
        
class CalibrationTimestamp(BaseModel):
    __tablename__ = 'calibration_timestamp'
    
    id = Column('id', Integer, primary_key=True)
    timestamp = Column('timestamp', Numeric(30, 10), primary_key=True)

    def __init__(self, ts):
        self.id = None
        self.timestamp = ts

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

class CalibrationTraining(BaseModel):
    __tablename__ = 'calibration_training'

    id = Column('id', Integer, primary_key = True)
    calibration_value = Column("calibration_value", Integer)
    ap_bssid = Column("bssid", String(256))
    ap_value_mean = Column("calibration_ap_value_mean", Numeric(25, 17))
    sigma = Column("sigma", Numeric(25, 17))
    #cp_value = Column("cp_value", Numeric(30, 10))

    def __init__(self, calibration_value, ap_bssid, ap_value_mean, sigma): #, cp_value):
        self.calibration_value = calibration_value
        self.ap_bssid = ap_bssid
        self.ap_value_mean = ap_value_mean
        self.sigma = sigma
        #self.cp_value = cp_value

    def __repr__(self):
        d = {}
        d['calibration_value'] = self.calibration_value
        d['bssid'] = self.ap_bssid
        d['ap_value_mean'] = self.ap_value_mean
        d['sigma'] = self.sigma
        #d['cp_value'] = self.cp_value
        return str(d)




def gaussian_cp(x, xmean, sigma):
    y = ((2.0 * np.pi) ** (-1.0/2.0)) * (np.e ** (((-1.0/2.0) * ((x - xmean) ** 2.0)) / (sigma ** 2.0)))
    return y

def training_ap(training_db):
    training_db.clear_calibration_training()
    value_list = training_db.query_calibration_value()

    #选择同一个房间号对应的所有采样时间点
    for v in value_list:
        print "Value : %d" % v
        timestamp_list = training_db.query_calibration_by_value(v)
        ap_no = len(timestamp_list)

        print "This value timesstamp Number : %d" % ap_no

        #选择同一个房间同一个时间采样点中的所有有效AP
        all_times_ap_list = []
        for t in timestamp_list:
            one_time_ap_list = training_db.query_calibration_by_value_timestamp(v, t)
            all_times_ap_list.extend(one_time_ap_list)
            

        training_ap_list = []
        for ap in all_times_ap_list:
            if all_times_ap_list.count(ap) >= ap_no * 0.9:
                if training_ap_list.count(ap) == 0:
                    training_ap_list.append(ap)

        print "Training AP Number : %d" % len(training_ap_list)

        #开始计算该房间号中所有有效AP的分布概率
        for ap in training_ap_list:
            one_ap_value_list = training_db.query_calibration_by_value_bssid(v, ap)
            one_ap_value_array_src = np.array(one_ap_value_list, dtype = np.float64)
            one_ap_value_array_des = np.array(one_ap_value_list, dtype = np.float64)
            one_ap_sigma_array = np.array(one_ap_value_list, dtype = np.float64)
            
            print "AP list is : %s" % one_ap_value_array_src

            #计算AP的物理信号值
            i = 0
            for j in one_ap_value_array_des:
                one_ap_value_array_des[i] = 10.0 ** (j / 10.0)
                i = i + 1

            #计算该房间区域内的AP信号平均值
            one_ap_value_mean = 10 * np.log10(one_ap_value_array_des.mean())

            print "One AP value mean is : %e" % one_ap_value_mean

            #根据信号平均值计算出各AP在该房间区域内的方差
            i = 0
            for j in one_ap_sigma_array:
                one_ap_sigma_array[i] = (one_ap_value_mean - one_ap_sigma_array[i]) ** 2.0
                i = i + 1

            one_ap_sigma_value = one_ap_sigma_array.mean()
            print "One AP sigma1 is : %e" % one_ap_sigma_value
            print "One AP sigma2 is : %e" % one_ap_sigma_value ** (1.0 / 2.0)

            #根据该房间内的AP信号平均值和方差计算各个AP在该区域内的概率密度
            #for j in one_ap_value_array_src:
            #    print j
            #    print "CP is : %e" % gaussian_cp(j, one_ap_value_mean, one_ap_sigma_value)

            #print "%e" % gaussian_cp(one_ap_value_mean, one_ap_value_mean, one_ap_sigma_value)

            #将区域ID与其对应的AP平均值和方差值存入数据库

            d = {}
            d['calibration_value'] = v
            d['bssid'] = ap
            d['ap_value_mean'] = float(one_ap_value_mean)
            d['sigma'] = float(one_ap_sigma_value)
            #d['cp_value'] = float(gaussian_cp(one_ap_value_mean, one_ap_value_mean, one_ap_sigma_value))
            training_db.insert_calibration_training(d)


def calibration_point(training_db):
    #从源数据库中得到区域ID和该区域的采样时间点
    value_list = training_db.query_calibration_value()
    print value_list

    #从源数据库中根据区域ID和该区域的采样时间点得到相应的bssid和AP值
    for v in value_list:
        print "Value : %d" % v
        timestamp_list = training_db.query_calibration_by_value(v)
        ap_no = len(timestamp_list)

        print "This value timesstamp Number : %d" % ap_no

        #选择同一个房间同一个时间采样点中的所有有效AP
        all_times_ap_list = []
        for t in timestamp_list:
            one_time_ap_list = training_db.query_calibration_by_value_timestamp(v, t)
            print "One value one times AP is : %s" % one_time_ap_list

            #开始计算概率......


if __name__ == "__main__":
    training_db = Mysql()
    #training_db.init_db()
    training_db.open_session()
    training_ap(training_db)
    calibration_point(training_db)
    training_db.close_session()
