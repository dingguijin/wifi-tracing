import  pymysql

class Mysql:
    conn = None
    cur = None

    def connect_mysql(self):
        self.conn =  pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='qwer#1234', db='wifi_tracing')

    def select_all(self):
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT * FROM calibration_original")
        q = self.cur.fetchall()
        return  q

    def close_db(self):
        self.cur.close()
        self.conn.close()

db = Mysql()
db.connect_mysql()
p = db.select_all()
for r in p:
   print r
db.close_db()
