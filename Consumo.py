import requests


resposta = requests.get("http://localhost:8080/SoundGate_/rest/SGWebService")
print(resposta.content)
