import MySQLdb as mysql
import re
from collections import defaultdict


def to_dict(data):
    result = dict()
    for elem in data:
        result[elem[0]] = elem
    return result


class DBconnect:

    def __init__(self, host, user, passwd, db):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db

    def __enter__(self):
        self.conn = mysql.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db)
        self.conn.set_character_set('utf8')
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
        if exc_val:
            raise


class CitizenDB:
    credentials = {
        "user": "root",
        "passwd": "pass"
    }
    db_name = None

    def __init__(self, db_name):
        self.db_name = db_name

    def create_table(self, table_name):
        db = mysql.connect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                           host="localhost")
        db.set_character_set('utf8')
        cursor = db.cursor()
        table_name = re.sub(r"[\s\[\]\(\)]\*,", "", table_name)  # to avoid some SQL inj
        cursor.execute("CREATE TABLE " + table_name + """(
                        citizen_id INT NOT NULL PRIMARY KEY,
                        town VARCHAR(100),
                        street VARCHAR(100),
                        building VARCHAR(100),
                        appartement INT,
                        name VARCHAR(100),
                        birth_date DATE,
                        gender ENUM('male', 'female'),
                        relatives VARCHAR(100)
                        );
        """)
        db.close()

    def fill_import(self, table_name, citizens):
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            table_name = re.sub(r"[\s\[\]\(\)]\*,", "", table_name)  # to avoid some SQL inj
            cursor = db.cursor()
            cursor.execute("CREATE TABLE " + table_name + """(
                                    citizen_id INT NOT NULL PRIMARY KEY,
                                    town VARCHAR(100),
                                    street VARCHAR(100),
                                    building VARCHAR(100),
                                    appartement INT,
                                    name VARCHAR(100),
                                    birth_date DATE,
                                    gender ENUM('male', 'female'),
                                    relatives VARCHAR(100)
                                    );
                    """)
            for citizen in citizens:
                citizens[citizen]["relatives"] = ','.join([str(x) for x in citizens[citizen]["relatives"]])
                cursor.execute("INSERT INTO " + table_name + " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               citizens[citizen].values())
            cursor.close()

    def get_next_id(self):
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM imports;")
            result = cursor.fetchone()[0]
            cursor.execute("UPDATE imports SET id=%s", (result+1,))
            cursor.close()

        return result

    def get_info(self, import_id):
        result = []
        keys = ("citizen_id", "town", "street", "building", "appartement", "name", "birth_date", "gender", "relatives")
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM import_" + str(import_id))
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                result.append(dict(zip(keys, data)))
                result[-1]["relatives"] = '[' + result[-1]["relatives"] + ']'
                result[-1]["birth_date"] = result[-1]["birth_date"].strftime("%d.%m.%Y")
            cursor.close()
        return result

    def get_birthdays_info(self, import_id):
        result = defaultdict(lambda: [])
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT citizen_id, birth_date, relatives FROM import_" + str(import_id))
            data = to_dict(cursor.fetchall())
            cursor.close()

        for elem in data:
            gifts = defaultdict(lambda: 0)
            for relative in data[elem][2].split(','):
                relative_id = int(relative)
                gifts[data[relative_id][1].month] += 1
            for month in gifts:
                result[str(month)].append({"citizen_id": elem, "presents": gifts[month]})

        return result



if __name__ == '__main__':
    data = CitizenDB("citizens")
    try:
        print(data.get_birthdays_info(60))
    except mysql.ProgrammingError as e:
        print(e)
