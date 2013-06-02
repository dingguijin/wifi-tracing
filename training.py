from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import CHAR, Integer, String, DateTime, Numeric, Float
from sqlalchemy.schema import ForeignKey
from sqlalchemy import distinct

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
        q = self.session.query(CalibrationOriginal.bssid, CalibrationOriginal.signal_strength).filter(CalibrationOriginal.calibration_value == value, CalibrationOriginal.calibration_timestamp_id == timestamp, CalibrationOriginal.signal_strength <= -35, CalibrationOriginal.signal_strength >= -95)

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




if __name__ == "__main__":
    training_db = Mysql()
    training_db.open_session()

    value_list = training_db.query_calibration_value()

    for v in value_list:
        print "Value : %d" % v
        timestamp_list = training_db.query_calibration_by_value(v)
        ap_no = len(timestamp_list)

        print "This value timesstamp Number : %d" % ap_no

        all_times_ap_list = []
        for t in timestamp_list:
            one_time_ap_list = training_db.query_calibration_by_value_timestamp(v, t)
            all_times_ap_list.extend(one_time_ap_list)
            
        training_ap_list = []
        for ap in all_times_ap_list:
            if all_times_ap_list.count(ap) >= ap_no * 0.7:
                if training_ap_list.count(ap) == 0:
                    training_ap_list.append(ap)

        print "Training AP Number : %d" % len(training_ap_list)

        for ap in training_ap_list:
            one_ap_value_list = training_db.query_calibration_by_value_bssid(v, ap)
            
            ap_training_sum_value = 0.0
            for i in one_ap_value_list:
                ap_training_sum_value = ap_training_sum_value + (0.1 ** i)

            ap_training_value = ap_training_sum_value / len(one_ap_value_list)
            print "AP bssid : %s => %f" % (ap, ap_training_value)


    training_db.close_session()
