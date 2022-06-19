from distutils.dep_util import newer_pairwise
import MySQLdb as mysql
from collections import defaultdict
from numpy import percentile
from datetime import date
from marshmallow import ValidationError
import json


from sqlalchemy import Column,Integer,String,Date,Enum,PrimaryKeyConstraint,Text,select,update
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
import enum

from citizen_db_old import to_dict

class Gender(enum.Enum):
    male = 'male'
    female = 'female'


Base = declarative_base()

class Citizen(Base):

    __tablename__ = 'import'
    __table_args__ = (PrimaryKeyConstraint('import_id','citizen_id',name='import_citizen_id'),)
    import_id = Column(Integer)
    citizen_id = Column(Integer)
    town = Column(String(100))
    street = Column(String(100))
    building = Column(String(100))
    apartment = Column(Integer)
    name = Column(String(100))
    birth_date = Column(Date)
    gender = Column(Enum(Gender))
    relatives = Column(Text)

class ImportId(Base):

    __tablename__ = 'imports'
    id = Column(Integer,primary_key=True)


class CitizenDB:

    def __init__(self,engine) -> None:
        self.engine = create_engine(engine, echo=True, future=True)

    
    def _2dict(self,row):
        keys = ("citizen_id", "town", "street", "building", "apartment", "name", "birth_date", "gender", "relatives")
        row = dict(row)['Citizen'].__dict__
        row["relatives"] = json.loads(row["relatives"])
        row["birth_date"] = row["birth_date"].strftime("%d.%m.%Y")
        row["gender"] = row["gender"].value
        return {key:row[key] for key in keys}


    def _age(self,birth_date):
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


    def fill_import(self, import_id, citizens):
        with Session(self.engine) as session:
            for citizen_id in citizens:
                citizens[citizen_id]["relatives"] = json.dumps(citizens[citizen_id]["relatives"])

                session.add(Citizen(
                    import_id=import_id,
                    **(citizens[citizen_id])
                ))
            session.commit()
            

    def get_next_id(self):
        with Session(self.engine) as session:
            id = session.query(ImportId).one()
            current_id = id.id
            id.id += 1
            session.commit()

        return current_id

    
    def get_info(self, import_id):
        
        result = []
        with Session(self.engine) as session:
            stmt = select(Citizen).where(Citizen.import_id == import_id)
            
            for row in session.execute(stmt):
                
                result.append(self._2dict(row))

        if not len(result):
            raise ValidationError("import_id doesn't exist")
                     
        return result


    def get_birthdays_info(self, import_id):
        result = dict()
        data = dict()
        for i in range(1,13):
            result[str(i)] = []
        with Session(self.engine) as session:
            stmt = select(Citizen.citizen_id,Citizen.birth_date,Citizen.relatives).where(Citizen.import_id == import_id)
            for row in session.execute(stmt):
                data[row.citizen_id] = (row.birth_date.month, row.relatives)

        if len(data) < 1:
            raise ValidationError("import_id doesn't exist")

        for elem in data:
            gifts = defaultdict(lambda: 0)
            for relative in json.loads(data[elem][1]):
                gifts[data[relative][0]] += 1
            for month in gifts:
                result[str(month)].append({"citizen_id": elem, "presents": gifts[month]})

        return result



    def get_statistics(self, import_id):
        result = []
        ages_in_town = defaultdict(lambda: [])

        with Session(self.engine) as session:
            stmt = select(Citizen.town,Citizen.birth_date).where(Citizen.import_id == import_id)
            for row in session.execute(stmt):
                ages_in_town[row.town].append(self._age(row.birth_date))
            if ages_in_town == {}:
                raise ValidationError("import_id doesn't exist")
        
        for town in ages_in_town:
            perc = percentile(ages_in_town[town], [50, 75, 99], interpolation='linear')
            result.append({"town": town, "p50": round(perc[0], 2), "p75": round(perc[1], 2), "p99": round(perc[2], 2)})
        return result



    def patch_user_data(self, import_id, citizen_id, data):
        import_id = int(import_id)
        citizen_id = int(citizen_id)
        with Session(self.engine) as session:
            if "relatives" in data:
                old_relatives = session.execute(select(Citizen.relatives).where(Citizen.import_id == import_id).where(Citizen.citizen_id == citizen_id)).one()
                old_relatives = set(json.loads(old_relatives.relatives))
                data["relatives"] = json.dumps(data["relatives"])
            stmt = update(Citizen).where(Citizen.import_id == import_id).where(Citizen.citizen_id == citizen_id).values(**data)
            session.execute(stmt)

            if "relatives" in data:
                new_relatives = set(json.loads(data["relatives"]))

                for elem in old_relatives - new_relatives - set([citizen_id]):
                    old_list = json.loads(session.execute(select(Citizen.relatives).where(Citizen.import_id == import_id).where(Citizen.citizen_id == elem)).one().relatives)
                    old_list.remove(citizen_id)
                    new_value = json.dumps(old_list)
                    session.execute(update(Citizen).where(Citizen.import_id == import_id).where(Citizen.citizen_id == elem).values(relatives=new_value))

                for elem in new_relatives - old_relatives - set([citizen_id]):
                    old_list = json.loads(session.execute(select(Citizen.relatives).where(Citizen.import_id == import_id).where(Citizen.citizen_id == elem)).one().relatives)
                    old_list.append(citizen_id)
                    new_value = json.dumps(old_list)
                    session.execute(update(Citizen).where(Citizen.import_id == import_id).where(Citizen.citizen_id == elem).values(relatives=new_value))
                
                

            stmt = select(Citizen).where(Citizen.import_id == import_id).where(Citizen.citizen_id == citizen_id)
            result = self._2dict(session.execute(stmt).one())
            session.commit()
        return result

            




if __name__ == '__main__':

    engine = create_engine("mysql://citizen_app:pass@localhost/citizens", echo=True, future=True)
    Base.metadata.create_all(engine)

    db = CitizenDB()


