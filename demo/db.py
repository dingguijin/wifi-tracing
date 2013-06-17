#!/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import *
from sqlalchemy.schema import ForeignKey
from sqlalchemy import distinct

DB_CONNECT_STRING = "mysql+pymysql://root:qwer#1234@127.0.0.1/wifi_tracing"

class Mysql:

    def __init__(self):
        self.engine = create_engine(DB_CONNECT_STRING, echo=False)
        self.DBSession = sessionmaker(bind=self.engine)
        self.session = None

    def open_session(self):
        self.session = self.DBSession()

    def close_session(self):
        if self.session:
            self.session.close()
            self.session = None

    def execute_sql_ret0(self, sql):
        self.session.execute(sql)

    def execute_sql_ret1(self, sql):
        q = self.session.execute(sql)
        
        ret = []
        for line in q:
            ret.append(line[0])

        return ret

    def execute_sql_ret2(self, sql):
        q = self.session.execute(sql)
        
        ret = []
        for line in q:
            ret.append([line[0], line[1]])

        return ret

    def execute_sql_ret3(self, sql):
        q = self.session.execute(sql)
        
        ret = []
        for line in q:
            ret.append([line[0], line[1], line[2]])

        return ret

    def execute_sql_ret4(self, sql):
        q = self.session.execute(sql)
        
        ret = []
        for line in q:
            ret.append([line[0], line[1], line[2], line[3]])

        return ret
