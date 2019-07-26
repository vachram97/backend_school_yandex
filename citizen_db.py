import MySQLdb as mysql


class Citizen_DB:

    def __init__(self, db_name):
        mysql.connect(user="root", passwd="pass", db=db_name, host="localhost")


if __name__ == '__main__':
    db = Citizen_DB("citizens")