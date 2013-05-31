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
        
    def query_calibration_by_value(self, value):
        q = self.session.query(distinct(CalibrationOriginal.calibration_timestamp_id)).filter(CalibrationOriginal.calibration_value == value)
        print q.count()
        return q
        
        
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

def test_insert_calibration(test_db):
    test_db.open_session()
    for i in range(1000):
        tu = datetime.datetime.now().timetuple()
        d = {}
        #d["timestamp"] = time.mktime(tu)
        d["timestamp"] = time.time()
        d["ssid"] = "ssid"
        d["bssid"] = "bssid"
        d["signal_strength"] = -100
        d["calibration_value"] = -1
        test_db.insert_calibration(d)
    test_db.close_session()

def test_constuct():
    pass

def test_calibration(db, value):
    db.open_session()
    q = db.query_calibration_by_value(value)
    db.close_session()

if __name__ == "__main__":
    test_db = Mysql()
    #test_db.drop_db()
    #test_db.init_db()
    #test_insert_calibration(test_db)
    test_calibration(test_db, 2)

