import requests
import datetime

url = "http://0.0.0.0:8080/imports"
data = [{"citizen_id": 1,
         "town": "Москва",
         "street": "Льва Толстого",
         "building": "16к7стр5",
         "appartement": 7,
         "name": "Иванов Иван Иванович",
         "birth_date": "01.01.2000",
         "gender": "male",
         "relatives": [1]},
        {"citizen_id": 2,
         "town": "Москва",
         "street": "Льва Толстого",
         "building": "16к7стр5",
         "appartement": 7,
         "name": "Иванов Иван Иванович",
         "birth_date": "01.01.200",
         "gender": "male",
         "relatives": [1]}
        ]
#print(requests.post(url, json=data).json())

data = [{"citizen_id": 1,
         "town": "Москва",
         "street": "Льва Толстого",
         "building": "16к7стр5",
         "appartement": 7,
         "name": "Иванов Иван Иванович",
         "birth_date": "01.01.2010",
         "gender": "male",
         "relatives": [1, 2]},
        {"citizen_id": 2,
         "town": "Москва",
         "street": "Льва Толстого",
         "building": "16к7стр5",
         "appartement": 7,
         "name": "Иванов Иван Иванович",
         "birth_date": "01.01.2000",
         "gender": "male",
         "relatives": [1]}
        ]
#print(requests.post(url, json=data).text)

data = {
    "town": "Kerch",
    "street": "Iosif"
}
#print(requests.patch(url+"/60/citizens/2", json=data).json())
#print(requests.get(url+"/60/citizens/birthdays").json())

data = []
for i in range(10000):
    data.append({"citizen_id": i,
         "town": "Москва",
         "street": "Льва Толстого",
         "building": "16к7стр5",
         "appartement": 7,
         "name": "Иванов Иван Иванович",
         "birth_date": "01.01.2010",
         "gender": "male",
         "relatives": [i]})

time = datetime.datetime.now()
print(requests.post(url, json=data).text)
print(datetime.datetime.now() - time)


