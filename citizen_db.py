import MySQLdb as mysql
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


def db_insert_row(cursor, import_id, values):
    cursor.execute("INSERT INTO import VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (import_id, *values))


class CitizenDB:
    db_name = None
    credentials = dict()

    def __init__(self, user, passwd, db_name):
        self.db_name = db_name
        self.credentials["user"] = user
        self.credentials["passwd"] = passwd

    def fill_import(self, import_id, citizens):

        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            for citizen in citizens:
                citizens[citizen]["relatives"] = json.dumps(citizens[citizen]["relatives"])
                db_insert_row(cursor, import_id, citizens[citizen].values())
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
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM import WHERE import_id=%s", (import_id,))
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                data = data[1:]
                result.append(dict(zip(keys, data)))
                result[-1]["relatives"] = json.loads(result[-1]["relatives"])
                result[-1]["birth_date"] = result[-1]["birth_date"].strftime("%d.%m.%Y")
            cursor.close()
            if not result:
                raise ValidationError("import_id doesn't exist")
        return result

    def get_birthdays_info(self, import_id):
        result = dict()
        for i in range(1, 13):
            result[str(i)] = []
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT citizen_id, birth_date, relatives FROM import WHERE import_id=%s", (import_id,))
            data = to_dict(cursor.fetchall())
            cursor.close()

        if not data:
            raise ValidationError("import_id doesn't exist")

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
            cursor.execute("SELECT town, birth_date FROM import WHERE import_id=%s", (import_id,))
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                ages_in_town[data[0]].append(age(data[1]))
            if ages_in_town == {}:
                raise ValidationError("import_id doesn't exist")
            cursor.close()
        for town in ages_in_town:
            perc = percentile(ages_in_town[town], [50, 75, 99], interpolation='linear')
            result.append({"town": town, "p50": round(perc[0], 2), "p75": round(perc[1], 2), "p99": round(perc[2], 2)})
        return result

    def patch_user_data(self, import_id, citizen_id, data):
        keys = ("citizen_id", "town", "street", "building", "apartment", "name", "birth_date", "gender", "relatives")
        import_id = int(import_id)
        citizen_id = int(citizen_id)
        with DBconnect(db=self.db_name, user=self.credentials["user"], passwd=self.credentials["passwd"],
                       host="localhost") as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM import WHERE import_id=%s AND citizen_id=%s", (import_id, citizen_id))
            old_data = cursor.fetchone()
            if not old_data:
                raise ValidationError("citizen doesn't exist")
            old_data = old_data[1:]
            citizen_data = dict(zip(keys, old_data))
            query = "UPDATE import SET "
            for elem in data:
                query += elem + "='" + str(data[elem]) + "' ,"
                citizen_data[elem] = data[elem]
            query = query[:-1] + " WHERE import_id=" + str(import_id) + " AND citizen_id=" + str(citizen_id)
            cursor.execute(query)
            if "relatives" in data:
                old_relatives = set(json.loads(old_data[8]))
                new_relatives = set(data["relatives"])
                for elem in old_relatives - new_relatives - set([citizen_id]):
                    cursor.execute("SELECT relatives FROM import WHERE import_id=%s AND citizen_id=%s", (import_id, elem))
                    old_list = json.loads(cursor.fetchone()[0])
                    old_list.remove(citizen_id)

                    cursor.execute("UPDATE import SET relatives='" + json.dumps(
                        old_list) + "' WHERE import_id=%s AND citizen_id=%s", (import_id, elem))

                for elem in new_relatives - old_relatives - set([citizen_id]):
                    cursor.execute("SELECT relatives FROM import WHERE import_id=%s AND citizen_id=%s", (import_id, elem))
                    old_list = json.loads(cursor.fetchone()[0])
                    old_list.append(citizen_id)
                    cursor.execute("UPDATE import SET relatives='" + json.dumps(
                        old_list) + "' WHERE import_id=%s AND citizen_id=%s", (import_id, elem))
            else:
                citizen_data["relatives"] = json.loads(citizen_data["relatives"])
            cursor.close()
        citizen_data["birth_date"] = citizen_data["birth_date"].strftime("%d.%m.%Y")
        return citizen_data




if __name__ == '__main__':
    data = CitizenDB("citizens")
    try:
        print(data.get_statistics(60))
    except mysql.ProgrammingError as e:
        print(e)
