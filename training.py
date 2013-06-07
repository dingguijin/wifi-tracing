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

    def query_training_value(self):
        q = self.session.query(distinct(CalibrationTraining.calibration_value))

        value_list = []
        for v in q:
            value_list.append(v[0])

        return value_list

    def query_training_ap_by_value(self, value):
        q = self.session.query(CalibrationTraining.ap_bssid).filter(CalibrationTraining.calibration_value == value)

        training_ap_list = []
        for t in q:
            training_ap_list.append(t[0])

        return training_ap_list

    def query_training_by_value_ap(self, value, ap):
        q = self.session.query(CalibrationTraining.ap_value_mean, CalibrationTraining.sigma).filter(CalibrationTraining.calibration_value == value, CalibrationTraining.ap_bssid == ap)
        mean_sigma_list = np.array(q[0], dtype = np.float64) 
        return mean_sigma_list
        
    def query_calibration_by_value(self, value):
        q = self.session.query(distinct(CalibrationOriginal.calibration_timestamp_id)).filter(CalibrationOriginal.calibration_value == value)

        timestamp_list = []
        for t in q:
            timestamp_list.append(t[0])

        return timestamp_list

    def query_calibration_by_value_timestamp2(self, value, timestamp):
        q = self.session.query(CalibrationOriginal.bssid, CalibrationOriginal.signal_strength).filter(CalibrationOriginal.calibration_value == value, CalibrationOriginal.calibration_timestamp_id == timestamp, CalibrationOriginal.signal_strength <= -30, CalibrationOriginal.signal_strength >= -100)

        ap_signal_list = []
        for ap in q:
            ap_signal_list.append([ap[0], ap[1]])

        return ap_signal_list

    def query_calibration_by_value_timestamp(self, value, timestamp):
        q = self.session.query(CalibrationOriginal.bssid, CalibrationOriginal.signal_strength).filter(CalibrationOriginal.calibration_value == value, CalibrationOriginal.calibration_timestamp_id == timestamp, CalibrationOriginal.signal_strength <= -30, CalibrationOriginal.signal_strength >= -100)

        ap_list = []
        for ap in q:
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
    X = stats.norm(loc = np.float64(xmean), scale = np.float64(sigma))
    y = X.pdf(np.float64(x))
    #y = ((2.0 * np.pi * sigma) ** (-1.0/2.0)) * (np.e ** (((-1.0/2.0) * ((x - xmean) ** 2.0)) / (sigma ** 2.0)))
    #y = ((2.0 * np.pi) ** (-1.0/2.0)) * (np.e ** (((-1.0/2.0) * ((x - xmean) ** 2.0)) / (sigma ** 2.0)))
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
            if all_times_ap_list.count(ap) >= ap_no * 0.90:
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
                one_ap_value_array_des[i] = np.float64(10.0 ** (j / 10.0))
                i = i + 1

            #计算该房间区域内的AP信号平均值
            one_ap_value_mean = np.float64(10.0 * np.log10(one_ap_value_array_des.mean()))

            print "One AP value mean is : %e" % one_ap_value_mean

            #根据信号平均值计算出各AP在该房间区域内的方差
            i = 0
            for j in one_ap_sigma_array:
                one_ap_sigma_array[i] = np.float64((one_ap_value_mean - one_ap_sigma_array[i]) ** 2.0)
                i = i + 1

            sigma_sum = np.float64(0.0)
            for j in one_ap_sigma_array:
                sigma_sum = np.float64(sigma_sum + j)

            one_ap_sigma_value = np.float64(sigma_sum / (len(one_ap_sigma_array) - 1))
            #one_ap_sigma_value = np.float64(sigma_sum / len(one_ap_sigma_array))
            #one_ap_sigma_value = one_ap_sigma_array.mean()
            print "One AP sigma1 is : %e" % one_ap_sigma_value
            print "One AP sigma2 is : %e" % one_ap_sigma_value ** (1.0 / 2.0)

            #将区域ID与其对应的AP平均值和方差值存入数据库
            d = {}
            d['calibration_value'] = v
            d['bssid'] = ap
            d['ap_value_mean'] = float(one_ap_value_mean)
            d['sigma'] = float(one_ap_sigma_value)
            training_db.insert_calibration_training(d)


def calibration_compute(training_db, src_ap_list, src_ap_signal_list):

    ret = {'value':-1, 'CP':0.0}

    cp_list = []
    cp_f = np.float64(0.0)
    training_value_list = training_db.query_training_value()
    for v in training_value_list:
        training_ap_list = training_db.query_training_ap_by_value(v)

        cp = np.float64(0.0)
        i = 0
        for src_ap in src_ap_list:
            #从源数据表中找到一个AP 检查该AP是否存在于训练表中
            if training_ap_list.count(src_ap) == 0:
                i = i + 1
                continue

            #如果源数据AP存在于训练表 查到该AP对应与训练表中的平均值和方差
            for ap in training_ap_list:
                if src_ap == ap:
                    mean_sigma = training_db.query_training_by_value_ap(v, ap)
            
            #计算源AP信号值与对应于训练表中AP的概率
            cp_t = np.float64(gaussian_cp(np.float64(src_ap_signal_list[i][1]), np.float64(mean_sigma[0]), np.float64(mean_sigma[1])))
            cp = cp + np.float64(cp_t)
            i = i + 1

        #print "value = %s cp = %e" % (v, cp)
        
        cp_list.append(np.float64(cp))

        if ret['CP'] < cp:
            ret['value'] = v
            ret['CP'] = cp

    cp_list.sort()
    #print "cp_list :", cp_list
    cp_max = np.float64(cp_list[-1])
    cp_max2 = np.float64(cp_list[-2])
    #print "cp_max :", cp_max, "cp_max2 :", cp_max2

    if cp_max2 != 0.0:
        cp_f = (cp_max - cp_max2) / cp_max2
        print "cp_f :", cp_f

    if cp_f > 0 and cp_f < 0.15:
        ret['value'] = -1
        ret['CP'] = -1

    return ret


def calibration_point(training_db):
    #从源数据库中得到区域ID和该区域的采样时间点
    value_list = training_db.query_calibration_value()
    print value_list

    #从源数据库中根据区域ID和该区域的采样时间点得到相应的bssid和AP值
    for v in value_list:
        #print "Value : %d" % v
        timestamp_list = training_db.query_calibration_by_value(v)
        ap_no = len(timestamp_list)

        #print "This value timesstamp Number : %d" % ap_no

        #选择同一个房间同一个时间采样点中的所有有效AP
        all_times_ap_list = []
        for t in timestamp_list:
            one_time_ap_list = training_db.query_calibration_by_value_timestamp(v, t)
            one_time_ap_signal_list = training_db.query_calibration_by_value_timestamp2(v, t)
            #print "** One value is : %s ** one times AP is : %s ** One time AP and signal is %s" % (v, one_time_ap_list, one_time_ap_signal_list)

            #开始计算位置概率......
            cp_v = calibration_compute(training_db, one_time_ap_list, one_time_ap_signal_list)
            print "Src value = %s time_id = %s >> CP %s" % (v, t, cp_v)

if __name__ == "__main__":
    training_db = Mysql()
    #training_db.init_db()
    training_db.open_session()
    #training_ap(training_db)
    calibration_point(training_db)
    training_db.close_session()
