import requests


def checar_passagem(cd):
    resposta = requests.get("http://localhost:8080/SoundGateWB/")
    print(resposta.text)

