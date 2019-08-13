import requests
import datetime
import pytest
import mimesis
from collections import defaultdict
import numpy as np
from jsondiff import diff
import json


def good_import_generator(n_citizens=20, n_relations=30):
    data = []
    address_generator = mimesis.Address('ru')
    number_generator = mimesis.Numbers()
    person_generator = mimesis.Person('ru')
    gender_generator = mimesis.Person('en')
    datetime_generator = mimesis.Datetime()
    for i in range(1, n_citizens + 1):
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
        relation = (number_generator.between(1, n_citizens), number_generator.between(1, n_citizens))
        while relation in relations or (relation[1], relation[0]) in relations:
            relation = (number_generator.between(1, n_citizens), number_generator.between(1, n_citizens))
        relations.add(relation)

        data[relation[0] - 1]["relatives"].append(relation[1])
        if relation[0] != relation[1]:
            data[relation[1] - 1]["relatives"].append(relation[0])
    return data


host = "http://0.0.0.0:8080"


@pytest.fixture(scope='class')
def good_import():
    data = good_import_generator()
    url = host + "/imports"
    response = requests.post(url, json=data)
    return {"data": data, "import_id": response.json()['data']['import_id']}


class TestPost:
    url = host + "/imports"

    def test_post(self):
        data = good_import_generator()
        assert requests.post(self.url, json=data).status_code == 201

    @pytest.mark.skip
    def test_post_10000(self):
        data = good_import_generator(10000, 100000)
        time = datetime.datetime.now()
        assert requests.post(self.url, json=data).status_code == 201
        assert datetime.datetime.now() - time < datetime.timedelta(seconds=10)

    def test_post_wrong_id(self):
        data = good_import_generator()
        data[10]['citizen_id'] = 12
        assert requests.post(self.url, json=data).status_code == 400

    def test_post_wrong_apartment(self):
        data = good_import_generator()
        data[10]['apartment'] = 'my_apartment'
        assert requests.post(self.url, json=data).status_code == 400

    def test_post_wrong_relatives(self):
        data = good_import_generator()
        data[10]['relatives'].append(1)
        assert requests.post(self.url, json=data).status_code == 400

    def test_post_with_get(self):
        response = requests.get(self.url)
        assert response.status_code == 405

    def test_post_with_slash(self):
        data = good_import_generator()
        response = requests.post(self.url + "/", json=data)
        assert response.status_code == 404 or response.status_code == 201


class TestGet:
    url = host + "/imports/{}/citizens"

    def test_get(self, good_import):
        import_id = good_import["import_id"]
        url = self.url.format(import_id)
        response = requests.get(url)
        assert response.status_code == 200
        assert response.json()["data"] == good_import["data"]

    def test_get_wrong_id(self, good_import):
        import_id = good_import["import_id"]
        url = self.url.format(import_id + 10000)
        response = requests.get(url)
        assert response.status_code == 400


class TestGetBirthdays:
    url = host + "/imports/{}/citizens/birthdays"

    def birthdays_answer(self, data):
        ans = dict()
        for i in range(12):
            ans[str(i + 1)] = []
        for i in range(len(data)):
            gifts = defaultdict(lambda: 0)
            for relative in data[i]["relatives"]:
                gifts[datetime.datetime.strptime(data[relative - 1]["birth_date"], "%d.%m.%Y").month] += 1
            for month in gifts:
                ans[str(month)].append({"citizen_id": i + 1, "presents": gifts[month]})
        return ans

    def test_birthdays(self, good_import):
        import_id = good_import["import_id"]
        url = self.url.format(import_id)
        response = requests.get(url)
        answer = self.birthdays_answer(good_import["data"])
        assert response.status_code == 200
        assert response.json()["data"] == answer

    def test_birthdays_wrong_id(self, good_import):
        import_id = good_import["import_id"]
        url = self.url.format(import_id + 1000)
        response = requests.get(url)
        assert response.status_code == 400


class TestGetStatistics:
    url = host + "/imports/{}/citizens/towns/stat/percentile/age"

    def stats_answer(self, data):
        ages_by_town = defaultdict(lambda: [])
        ans = []
        for citizen in data:
            ages_by_town[citizen["town"]].append(self.age(citizen["birth_date"]))

        for town in ages_by_town:
            stats = np.percentile(ages_by_town[town], [50, 75, 99], interpolation='linear')
            ans.append({"town": town, "p50": stats[0], "p75": stats[1], "p99": stats[2]})

        return ans

    def age(self, birth_date):
        birth_date = datetime.datetime.strptime(birth_date, "%d.%m.%Y")
        today = datetime.date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def test_statistics(self, good_import):
        import_id = good_import["import_id"]
        url = self.url.format(import_id)
        response = requests.get(url)
        answer = self.stats_answer(good_import["data"])
        assert response.status_code == 200
        assert response.json()["data"] == answer

    def test_statistics_wrong_id(self, good_import):
        import_id = good_import["import_id"]
        url = self.url.format(import_id + 1000)
        response = requests.get(url)
        assert response.status_code == 400


class TestPatchData:
    url = host + "/imports/{}/citizens/{}"

    def update(self, data, new_data, citizen_id):

        for field in new_data:
            if field != 'relatives':
                data[citizen_id - 1][field] = new_data[field]
            else:
                for relative in data[citizen_id - 1]["relatives"]:
                    data[relative - 1]["relatives"].remove(citizen_id)
                for new_relative in new_data["relatives"]:
                    data[new_relative - 1]["relatives"].append(citizen_id)
                data[citizen_id - 1]["relatives"] = new_data["relatives"]

        return data

    def citizen_is_equal(self, first, second):
        for key in first:
            if key == 'relatives':
                try:
                    if set(first[key]) ^ set(second[key]) != set():
                        return False
                except KeyError:
                    return False
            else:
                try:
                    if first[key] != second[key]:
                        return False
                except KeyError:
                    return False
        return True

    def data_is_equal(self, first, second):
        if len(first) != len(second):
            return False

        for i in range(len(first)):
            if not self.citizen_is_equal(first[i], second[i]):
                return False
        return True

    test_data = [(1, {"town": "Monreal"}),
                 (2, {"building": "1384"}),
                 (3, {"relatives": [1, 2, 4, 5, 6, 7]}),
                 (4, {"apartment": 45}),
                 (5, {"name": "Иванов Иван Иванович"}),
                 (6, {"street": "Московское ш"}),
                 (7, {"gender": "male"}),
                 (7, {"gender": "female"}),
                 (8, {"birth_date": "01.01.2010"})
                 ]

    @pytest.mark.parametrize("citizen_id, new_data", test_data)
    def test_patch(self, good_import, citizen_id, new_data):
        import_id = good_import["import_id"]

        url = self.url.format(import_id, citizen_id)
        updated_data = self.update(good_import["data"], new_data, citizen_id)
        response = requests.patch(url, json=new_data)
        assert response.status_code == 200
        assert self.citizen_is_equal(updated_data[citizen_id - 1], response.json()["data"])
        response = requests.get(host + "/imports/{}/citizens".format(import_id))
        assert response.status_code == 200
        assert self.data_is_equal(updated_data, response.json()["data"])

    test_wrong_data = [(1, {"town": 44}),
                       (2, {"building": []}),
                       (3, {"relatives": [1, 1, 4, 5, 6, 7]}),
                       (4, {"apartment": "no"}),
                       (5, {"name": 33}),
                       (6, {"street": {"name": "hello"}}),
                       (7, {"gender": "not_male"}),
                       (7, {"gender": "not_female"}),
                       (8, {"birth_date": "2010.01.01"})
                       ]

    @pytest.mark.parametrize("citizen_id, new_data", test_wrong_data)
    def test_patch_wrong_data(self, good_import, citizen_id, new_data):
        import_id = good_import["import_id"]

        url = self.url.format(import_id, citizen_id)
        response = requests.patch(url, json=new_data)
        assert response.status_code == 400


def test_wrong_path():
    response = requests.get(host)
    assert response.status_code == 404
