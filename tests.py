import requests

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
#print(requests.patch(url+"/1/citizens/2", json=data))
print(requests.get(url+"/61/citizens").json())
