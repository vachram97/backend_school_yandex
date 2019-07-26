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
         "relatives": [2, 28]},
        {"citizen_id": 1,
         "town": "Москва",
         "street": "Льва Толстого",
         "building": "16к7стр5",
         "appartement": 7,
         "name": "Иванов Иван Иванович",
         "birth_date": "01.01.2000",
         "gender": "male",
         "relatives": [2, 28]}
        ]
print(requests.post(url, json=data))
