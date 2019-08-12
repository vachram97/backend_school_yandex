import MySQLdb as mysql
import re
from collections import defaultdict
from numpy import percentile
from datetime import date
from marshmallow import ValidationError
import json


def to_dict(data):
    result = dict()
    for elem in data:
        result[elem[0]] = elem
    return result


def age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


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


def db_insert_row(cursor, table_name, values):
    cursor.execute("INSERT INTO " + table_name + " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", values)


def db_create_table(cursor, table_name):
    cursor.execute("CREATE TABLE " + table_name + """(
                            citizen_id INT NOT NULL PRIMARY KEY,
                            town VARCHAR(100) NOT NULL,
                            street VARCHAR(100) NOT NULL,
                            building VARCHAR(100) NOT NULL,
                            apartment INT NOT NULL ,
                            name VARCHAR(100),
                            birth_date DATE,
                            gender ENUM('male', 'female'),
                            relatives TEXT
                                        );
                        """)


class CitizenDB:
    db_name = None
    credentials = dict()

    def __init__(self, user, passwd, db_name):
        self.db_name = db_name
        self.credentials["user"] = user
        self.credentials["passwd"] = passwd

    def fill_import(self, table_name, citizens):

        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            table_name = re.sub(r"[\s\[\]()]\*,;", "", table_name)  # to avoid some SQL inj
            cursor = db.cursor()
            db_create_table(cursor, table_name)
            for citizen in citizens:
                citizens[citizen]["relatives"] = json.dumps(citizens[citizen]["relatives"])
                db_insert_row(cursor, table_name, citizens[citizen].values())
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
        keys = ("citizen_id", "town", "street", "building", "apartment", "name", "birth_date", "gender", "relatives")
        table_name = "import_" + str(import_id)
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM " + table_name)
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                result.append(dict(zip(keys, data)))
                result[-1]["relatives"] = json.loads(result[-1]["relatives"])
                result[-1]["birth_date"] = result[-1]["birth_date"].strftime("%d.%m.%Y")
            cursor.close()
        return result

    def get_birthdays_info(self, import_id):
        result = dict()
        for i in range(1, 13):
            result[str(i)] = []
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT citizen_id, birth_date, relatives FROM import_" + str(import_id))
            data = to_dict(cursor.fetchall())
            cursor.close()

        for elem in data:
            gifts = defaultdict(lambda: 0)
            for relative in json.loads(data[elem][2]):
                gifts[data[relative][1].month] += 1
            for month in gifts:
                result[str(month)].append({"citizen_id": elem, "presents": gifts[month]})

        return result

    def get_statistics(self, import_id):
        result = []
        ages_in_town = defaultdict(lambda: [])
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT town, birth_date FROM import_" + str(import_id))
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                ages_in_town[data[0]].append(age(data[1]))
            cursor.close()
        for town in ages_in_town:
            perc = percentile(ages_in_town[town], [50, 75, 99], interpolation='linear')
            result.append({"town": town, "p50": perc[0], "p75": perc[1], "p99": perc[2]})
        return result

    def patch_user_data(self, import_id, citizen_id, data):
        keys = ("citizen_id", "town", "street", "building", "apartment", "name", "birth_date", "gender", "relatives")
        import_id = int(import_id)
        citizen_id = int(citizen_id)
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM import_" + str(import_id) + " WHERE citizen_id=%s", (citizen_id,))
            old_data = cursor.fetchone()
            if not old_data:
                raise ValidationError("id doesn't exist")
            citizen_data = dict(zip(keys, old_data))
            query = "UPDATE import_" + str(import_id) + ' SET '
            for elem in data:
                query += elem + "='" + str(data[elem]) + "' ,"
                citizen_data[elem] = data[elem]
            query = query[:-1] + " WHERE citizen_id=" + str(citizen_id)
            cursor.execute(query)
            if "relatives" in data:
                old_relatives = set(json.loads(old_data[8]))
                new_relatives = set(data["relatives"])
                for elem in old_relatives - new_relatives:
                    cursor.execute("SELECT relatives FROM import_" + str(import_id) + " WHERE citizen_id=%s", (elem,))
                    old_list = json.loads(cursor.fetchone()[0])
                    old_list.remove(citizen_id)

                    cursor.execute("UPDATE import_" + str(import_id) + " SET relatives=" + json.dumps(
                        old_list) + "WHERE citizen_id=%s", (elem,))

                for elem in new_relatives - old_relatives:
                    cursor.execute("SELECT relatives FROM import_" + str(import_id) + " WHERE citizen_id=%s", (elem,))
                    old_list = json.loads(cursor.fetchone()[0])
                    old_list.append(citizen_id)
                    cursor.execute("UPDATE import_" + str(import_id) + " SET relatives=" + json.dumps(
                        old_list) + " WHERE citizen_id=%s", (elem,))

            cursor.close()
        citizen_data["relatives"] = json.loads(citizen_data["relatives"])
        citizen_data["birth_date"] = citizen_data["birth_date"].strftime("%d.%m.%Y")
        return citizen_data




if __name__ == '__main__':
    data = CitizenDB("citizens")
    try:
        print(data.get_statistics(60))
    except mysql.ProgrammingError as e:
        print(e)
