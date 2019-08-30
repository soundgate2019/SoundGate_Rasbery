from chirpsdk import ChirpConnect, CallbackSet
import chirpsdk
import Consumo
import sys
import time
import RPi.GPIO as GPIO

chirp = ChirpConnect(key="0cDCbED05BdFEACad7A9AeFBD",
                     secret="14f10FE0c6dD2c9B14DC3a739EAE42AF5E363BD339CfCDEb3B",
                     config="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");
recebido = False
GPIO.setmode(GPIO.BCM)
vermelho = 26
amarelo = 13
verde = 6
botao = 17
GPIO.setup(botao, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(vermelho, GPIO.OUT)
GPIO.setup(amarelo, GPIO.OUT)
GPIO.setup(verde, GPIO.OUT)


class Callbacks(CallbackSet):
    global amarelo
    global verde

    def on_sent(self, payload, channel):
        print(f"mandei : {payload}")
        identifier = payload.decode('utf-8')
        print(identifier)

    def on_receiving(self, channel):
        print('Receiving data [ch{ch}]'.format(ch=channel))

    def on_received(self, payload, channel):
        if payload is not None:
            global recebido
            GPIO.output(amarelo, False)
            GPIO.output(verde, True)
            identifier = payload.decode('utf-8')
            print(identifier)
            recebido = True
        else:
            print('Decode failed')


def chirpe():
    global chirp
    global recebido
    global vermelho
    global amarelo
    GPIO.output(vermelho, False)
    GPIO.output(amarelo, True)
    # chirp.input_sample_rate = 32000
    print(chirp.audio.query_devices())
    chirp.set_callbacks(Callbacks())
    chirp.start()
    mensagem = 'hello'
    dados = bytearray([ord(ch) for ch in mensagem])
    chirp.send(dados)

    termino = time.time() + 20
    while not recebido and time.time() < termino:
        time.sleep(0.1)
        sys.stdout.flush()
    time.sleep(0.2)
    chirp.stop()
    recebido = False
    GPIO.output(verde, False)


while True:
    GPIO.output(vermelho, True)
    while not GPIO.input(botao):
        print("oi")
        chirpe()
        time.sleep(0.1)
    time.sleep(0.1)


