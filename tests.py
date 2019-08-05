import requests
import datetime
import pytest
import mimesis
from collections import defaultdict
import numpy as np


@pytest.fixture(scope='class')
def host_post():
    return "http://0.0.0.0:8080/imports"

@pytest.fixture(scope='module')
def host():
    return "http://0.0.0.0:8080"


def birthdays_answer(data):
    ans = dict()
    for i in range(12):
        ans[str(i+1)] = []
    for i in range(len(data)):
        gifts = defaultdict(lambda: 0)
        for relative in data[i]["relatives"]:
            gifts[datetime.datetime.strptime(data[relative-1]["birth_date"], "%d.%m.%Y").month]+=1
        for month in gifts:
            ans[str(month)].append({"citizen_id": i+1, "presents": gifts[month]})
    return ans


def age(birth_date):
    today = datetime.date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def stats_answer(data):
    raise NotImplementedError


def good_import_generator(n_citizens=20, n_relations=30):
    data = []
    address_generator = mimesis.Address('ru')
    number_generator = mimesis.Numbers()
    person_generator = mimesis.Person('ru')
    gender_generator = mimesis.Person('en')
    datetime_generator = mimesis.Datetime()
    for i in range(1, n_citizens+1):
        street, building = address_generator.address().rsplit(' ', maxsplit=1)
        gender = gender_generator.gender().lower()
        while gender != 'male' and gender != 'female':
            gender = gender_generator.gender().lower()
        data.append({
            "citizen_id": i,
            "town": address_generator.city(),
            "street": street,
            "building": building,
            "apartment": number_generator.between(1, 100000),
            "name": person_generator.full_name(),
            "birth_date": datetime_generator.date(1900, 2018).strftime("%d.%m.%Y"),
            "gender": gender,
            "relatives": []})
    relations = set()
    for i in range(n_relations):
        relation = (number_generator.between(1,n_citizens), number_generator.between(1,n_citizens))
        while relation in relations:
            relation = (number_generator.between(1, n_citizens), number_generator.between(1, n_citizens))
        relations.add(relation)
        data[relation[0]-1]["relatives"].append(relation[1])
        data[relation[1]-1]["relatives"].append(relation[0])
    return data


@pytest.fixture(scope='class')
def good_import(host):
    data = good_import_generator()
    url = host + "/imports"
    response = requests.post(url, json=data)
    return {"data": data, "import_id": response.json()['data']['import_id']}


class TestPost:

    def test_post(self, host_post):
        data = good_import_generator()
        assert requests.post(host_post, json=data).status_code == 201

    def test_post_10000(self, host_post):
        data = good_import_generator(10000, 100000)
        time = datetime.datetime.now()
        assert requests.post(host_post, json=data).status_code == 201
        assert datetime.datetime.now() - time < datetime.timedelta(seconds=10)

    def test_post_wrong_id(self, host_post):
        data = good_import_generator()
        data[10]['citizen_id'] = 12
        assert requests.post(host_post, json=data).status_code == 400


class TestGet:

    def test_get(self, host, good_import):
        import_id = good_import["import_id"]
        url = host + "/imports/" + str(import_id) + "/citizens"
        response = requests.get(url)
        assert response.status_code == 200
        assert response.json()["data"] == good_import["data"]

    def test_get_wrong_id(self, host, good_import):
        import_id = good_import["import_id"]
        url = host + "/imports/" + str(import_id + 10000) + "/citizens"
        response = requests.get(url)
        assert response.status_code == 400


class TestGetBirthdays:

    def test_birthdays(self, host, good_import):
        import_id = good_import["import_id"]
        url = host + "/imports/" + str(import_id) + "/citizens/birthdays"
        response = requests.get(url)
        answer = birthdays_answer(good_import["data"])
        assert response.status_code == 200
        assert response.json()["data"] == answer

    def test_birthdays_wrong_id(self, host, good_import):
        import_id = good_import["import_id"]
        url = host + "/imports/" + str(import_id+1000) + "/citizens/birthdays"
        response = requests.get(url)
        assert response.status_code == 400




def a_test_statistics(host, good_import):
    import_id = good_import["import_id"]
    url = host + "/imports/" + str(import_id) + "/citizens/towns/stat/percentile/age"
    response = requests.get(url)
    answer = stats_answer(good_import["data"])
    assert response.json()["data"] == answer
