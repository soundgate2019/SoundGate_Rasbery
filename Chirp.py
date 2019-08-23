from chirpsdk import ChirpConnect, CallbackSet
import chirpsdk
import sys
import time
chirp = ChirpConnect(debug=True, key="544c4dC370CEAf0df0d4C23E6", secret="BAa70CdaaAA5e9E43A46bfF1D99Ae5DEB0c0Aa4b36dfDB9fD0",
                     config="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")
recebido = False
chirp.audio.wav_filename = 'C:\\debug\\teste.wav'
print(chirpsdk.CHIRP_CONNECT_STATE_NOT_CREATED)

class Callbacks(CallbackSet):
    def on_sent(self, payload, channel):
        print(f"mandei : {payload}")
        identifier = payload.decode('utf-8')
        print(identifier)

    def on_receiving(self, channel):
        print('Receiving data [ch{ch}]'.format(ch=channel))

    def on_received(self, payload, channel):
        print("algo")
        if payload is not None:
            global recebido
            identifier = payload.decode('utf-8')
            print('Received: ' + identifier)
            recebido = True
        else:
            print('Decode failed')

    def on_state_changed(self, old, new):
        print(old, new)


#chirp.input_sample_rate = 32000
chirp.set_callbacks(Callbacks())
chirp.start()
mensagem = 'hello'
dados = bytearray([ord(ch) for ch in mensagem])

termino = time.time()+20
try:
    while not recebido and time.time() < termino:
        time.sleep(0.1)
        sys.stdout.write('.')
        sys.stdout.flush()
except KeyboardInterrupt:
        print('Exiting')

chirp.stop()
