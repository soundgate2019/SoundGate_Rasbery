# ------------------------------------------------------------------------
#
#  This file is part of the Chirp Python SDK.
#  For full information on usage and licensing, see https://chirp.io
#
#  Copyright (c) 2011-2018, Asio Ltd.
#  All rights reserved.
#
# ------------------------------------------------------------------------
import os
import struct
import time
import uuid
from . import libconnect, __version__

import configparser
from ctypes import (
    Structure, CFUNCTYPE, POINTER, pointer,
    c_char, c_char_p, c_uint8, c_uint32, c_uint64,
    c_short, c_float, c_void_p, c_bool, c_size_t,
    cast
)
from datetime import datetime
from platform import architecture
from random import randrange

from .audio import Audio
from .exceptions import ConnectError
from .network import (
    get_config_from_network,
    create_instantiate,
    create_send,
    create_receive
)
from _connect import (
    CHIRP_CONNECT_STATE_STOPPED,
    CHIRP_CONNECT_STATE_PAUSED,
    CHIRP_CONNECT_STATE_RUNNING,
    CHIRP_CONNECT_STATE_SENDING,
    CHIRP_CONNECT_STATE_RECEIVING,
    CHIRP_CONNECT_STATE_NOT_CREATED,
)

CHIRP_CONNECT_STATE = {
    CHIRP_CONNECT_STATE_STOPPED: 'Stopped',
    CHIRP_CONNECT_STATE_PAUSED: 'Paused',
    CHIRP_CONNECT_STATE_RUNNING: 'Running',
    CHIRP_CONNECT_STATE_SENDING: 'Sending',
    CHIRP_CONNECT_STATE_RECEIVING: 'Receiving',
    CHIRP_CONNECT_STATE_NOT_CREATED: 'Not Created'
}

# ------------------------------------------------------------------------
# Callback function pointers
# ------------------------------------------------------------------------
ChirpConnectCallback = CFUNCTYPE(None, c_void_p, POINTER(c_uint8), c_size_t, c_uint8)
ChirpConnectStateCallback = CFUNCTYPE(None, c_void_p, c_uint8, c_uint8)


class ChirpConnect(Structure):
    pass


class ChirpConnectCallbackSet(Structure):
    _fields_ = [
        ("on_state_changed", ChirpConnectStateCallback),
        ("on_sending", ChirpConnectCallback),
        ("on_sent", ChirpConnectCallback),
        ("on_receiving", ChirpConnectCallback),
        ("on_received", ChirpConnectCallback)
    ]

    def __init__(self, sdk):
        self.sdk = sdk
        self.state_changed_fn = ChirpConnectStateCallback(self.state_changed)
        self.sending_fn = ChirpConnectCallback(self.sending)
        self.sent_fn = ChirpConnectCallback(self.sent)
        self.receiving_fn = ChirpConnectCallback(self.receiving)
        self.received_fn = ChirpConnectCallback(self.received)
        super(ChirpConnectCallbackSet, self).__init__(
            self.state_changed_fn, self.sending_fn, self.sent_fn,
            self.receiving_fn, self.received_fn
        )

    def state_changed(self, cptr, old, new):
        self.sdk.callbacks.on_state_changed(old, new)

    def sending(self, cptr, data, length, channel):
        payload = _Payload(self.sdk, data[:length])
        self.sdk.callbacks.on_sending(payload if length else None, channel)

    def sent(self, cptr, data, length, channel):
        payload = _Payload(self.sdk, data[:length])
        self.sdk.callbacks.on_sent(payload if length else None, channel)

    def receiving(self, cptr, data, length, channel):
        self.sdk.callbacks.on_receiving(channel)

    def received(self, cptr, data, length, channel):
        payload = _Payload(self.sdk, data[:length])
        self.sdk.callbacks.on_received(payload if length else None, channel)
        if not self.sdk.is_offline:
            create_receive(
                self.sdk.key, self.sdk.secret, self.sdk._uid,
                length, self.sdk.protocol_name, self.sdk.protocol_version)


# ------------------------------------------------------------------------
# Symbol bindings: Utils
# ------------------------------------------------------------------------
libconnect.chirp_connect_get_library_name.restype = c_char_p
libconnect.chirp_connect_get_version.restype = c_char_p
libconnect.chirp_connect_get_build_number.restype = c_char_p
libconnect.chirp_connect_error_code_to_string.argtypes = [c_uint8]
libconnect.chirp_connect_error_code_to_string.restype = c_char_p
libconnect.chirp_connect_trigger_callbacks.argtypes = [c_void_p, POINTER(c_uint8), c_size_t]
libconnect.chirp_connect_is_offline_mode.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_is_offline_mode.restype = c_bool
libconnect.chirp_connect_free.argtypes = [c_void_p]

# ------------------------------------------------------------------------
# Symbol bindings: Getters & Setters
# ------------------------------------------------------------------------
libconnect.new_chirp_connect.argtypes = [c_char_p, c_char_p]
libconnect.new_chirp_connect.restype = POINTER(ChirpConnect)
libconnect.del_chirp_connect.argtypes = [POINTER(POINTER(ChirpConnect))]
libconnect.del_chirp_connect.restype = c_uint8
libconnect.chirp_connect_set_config.argtypes = [POINTER(ChirpConnect), c_char_p]
libconnect.chirp_connect_set_config.restype = c_uint8
libconnect.chirp_connect_set_random_seed.argtypes = [POINTER(ChirpConnect), c_uint32]
libconnect.chirp_connect_set_random_seed.restype = c_uint8
libconnect.chirp_connect_set_volume.argtypes = [POINTER(ChirpConnect), c_float]
libconnect.chirp_connect_set_volume.restype = c_uint8
libconnect.chirp_connect_get_volume.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_volume.restype = c_float
libconnect.chirp_connect_set_input_sample_rate.argtypes = [POINTER(ChirpConnect), c_uint32]
libconnect.chirp_connect_set_input_sample_rate.restype = c_uint8
libconnect.chirp_connect_get_input_sample_rate.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_input_sample_rate.restype = c_uint32
libconnect.chirp_connect_set_output_sample_rate.argtypes = [POINTER(ChirpConnect), c_uint32]
libconnect.chirp_connect_set_output_sample_rate.restype = c_uint8
libconnect.chirp_connect_get_output_sample_rate.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_output_sample_rate.restype = c_uint32
libconnect.chirp_connect_get_state.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_state.restype = c_uint8
libconnect.chirp_connect_set_auto_mute.argtypes = [POINTER(ChirpConnect), c_bool]
libconnect.chirp_connect_set_auto_mute.restype = c_uint8
libconnect.chirp_connect_get_auto_mute.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_auto_mute.restype = c_bool
libconnect.chirp_connect_get_protocol_name.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_protocol_name.restype = c_char_p
libconnect.chirp_connect_get_duration_for_payload_length.argtypes = [POINTER(ChirpConnect), c_size_t]
libconnect.chirp_connect_get_duration_for_payload_length.restype = c_float
libconnect.chirp_connect_get_protocol_version.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_protocol_version.restype = c_uint8
libconnect.chirp_connect_get_expiry_time.argtypes = [POINTER(ChirpConnect)]
if architecture()[0] == '32bit':  # Determine size of time_t
    libconnect.chirp_connect_get_expiry_time.restype = c_uint32
else:
    libconnect.chirp_connect_get_expiry_time.restype = c_uint64
libconnect.chirp_connect_get_state_for_channel.argtypes = [POINTER(ChirpConnect), c_uint8]
libconnect.chirp_connect_get_state_for_channel.restype = c_uint8
libconnect.chirp_connect_get_transmission_channel.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_transmission_channel.restype = c_uint8
libconnect.chirp_connect_set_transmission_channel.argtypes = [POINTER(ChirpConnect), c_uint8]
libconnect.chirp_connect_set_transmission_channel.restype = c_uint8
libconnect.chirp_connect_get_channel_count.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_channel_count.restype = c_uint8

# ------------------------------------------------------------------------
# Symbol bindings: States
# ------------------------------------------------------------------------
libconnect.chirp_connect_start.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_start.restype = c_uint8
libconnect.chirp_connect_pause.argtypes = [POINTER(ChirpConnect), c_bool]
libconnect.chirp_connect_pause.restype = c_uint8
libconnect.chirp_connect_stop.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_stop.restype = c_uint8

# ------------------------------------------------------------------------
# Symbol bindings: Callbacks
# ------------------------------------------------------------------------
libconnect.chirp_connect_set_callbacks.argtypes = [POINTER(ChirpConnect), ChirpConnectCallbackSet]
libconnect.chirp_connect_set_callbacks.restype = c_uint8
libconnect.chirp_connect_set_callback_ptr.argtypes = [POINTER(ChirpConnect), c_void_p]
libconnect.chirp_connect_set_callback_ptr.restype = c_uint8

# ------------------------------------------------------------------------
# Symbol bindings: Processing
# ------------------------------------------------------------------------
libconnect.chirp_connect_process_input.argtypes = [POINTER(ChirpConnect), POINTER(c_float), c_size_t]
libconnect.chirp_connect_process_input.restype = c_uint8
libconnect.chirp_connect_process_output.argtypes = [POINTER(ChirpConnect), POINTER(c_float), c_size_t]
libconnect.chirp_connect_process_output.restype = c_uint8
libconnect.chirp_connect_process_shorts_input.argtypes = [POINTER(ChirpConnect), POINTER(c_short), c_size_t]
libconnect.chirp_connect_process_shorts_input.restype = c_uint8
libconnect.chirp_connect_process_shorts_output.argtypes = [POINTER(ChirpConnect), POINTER(c_short), c_size_t]
libconnect.chirp_connect_process_shorts_output.restype = c_uint8

# ------------------------------------------------------------------------
# Symbol bindings: Payload
# ------------------------------------------------------------------------
libconnect.chirp_connect_get_max_payload_length.argtypes = [POINTER(ChirpConnect)]
libconnect.chirp_connect_get_max_payload_length.restype = c_size_t
libconnect.chirp_connect_random_payload.argtypes = [POINTER(ChirpConnect), POINTER(c_size_t)]
libconnect.chirp_connect_random_payload.restype = POINTER(c_uint8)
libconnect.chirp_connect_is_valid.argtypes = [POINTER(ChirpConnect), POINTER(c_uint8), c_size_t]
libconnect.chirp_connect_is_valid.restype = c_uint8
libconnect.chirp_connect_as_string.argtypes = [POINTER(ChirpConnect), POINTER(c_uint8), c_size_t]
libconnect.chirp_connect_as_string.restype = POINTER(c_char)
libconnect.chirp_connect_send.argtypes = [POINTER(ChirpConnect), POINTER(c_uint8), c_size_t]
libconnect.chirp_connect_send.restype = c_uint8


def get_unique_id():
    """ Get a unique identifier for this device """
    config = configparser.ConfigParser()
    path = os.path.join(os.path.expanduser('~'), '.chirp.ini')
    config.read(path)
    if not config.has_section('default'):
        config.add_section('default')
        config.set('default', 'client_id', str(uuid.uuid4()))
        with open(path, 'w') as cf:
            config.write(cf)
    return config['default']['client_id']


class _Payload(bytearray):
    """
    A Chirp Payload.
    Subclass of built in type - bytearray.
    """
    def __init__(self, sdk, *args, **kwargs):
        self._sdk = sdk
        self.max_length = self._sdk.max_payload_length
        super(_Payload, self).__init__(*args, **kwargs)
        if len(self) > self.max_length:
            raise ValueError('Payload has a maximum length of {}'.format(self.max_length))

    def __str__(self):
        return self._sdk.as_string(self)

    def __eq__(self, other):
        return list(self) == list(other)

    def isvalid(self):
        return self._sdk.is_valid(self)

    def extend(self, data):
        self.max_length = self._sdk.max_payload_length
        if len(self) + len(data) > self.max_length:
            raise ValueError('Payload has a maximum length of {}'.format(self.max_length))
        super(_Payload, self).extend(data)


class CallbackSet(object):
    """
    An abstract class to implement callback methods.

    The ChirpConnectSDK will call these methods when it is
    changing state, or is sending/receiving data. To handle
    data transmission you should inherit this, and assign
    it to the `callbacks` attribute of the SDK after loading
    the config.
    """
    def on_state_changed(self, old, new):
        """
        Called when the state of Chirp Library has changed.

        Args:
            old (str): Previous state
            new (str): Current state
        """
        pass

    def on_sending(self, payload, channel):
        """
        Called when the Chirp Library has begun sending data.

        Args:
            payload (Payload): The Chirp Payload (bytearray)
            channel (int): The channel on which the data is being sent
        """
        pass

    def on_sent(self, payload, channel):
        """
        Called when the Chirp Library has sent the whole payload.

        Args:
            payload (Payload): The Chirp Payload (bytearray)
            channel (int): The channel on which the data is sent
        """
        pass

    def on_receiving(self, channel):
        """
        Called when the Chirp Library hears the start of a payload.

        Args:
            channel (int): The channel on which the data is being received
        """
        pass

    def on_received(self, payload, channel):
        """
        Called when the Chirp Library has decoded a full payload.
        Note: A length of 0 indicates a failed decode.

        Args:
            payload (Payload): The Chirp Payload (bytearray)
            channel (int): The channel on which the data has being received
        """
        pass


class AudioSet(object):
    """
    An abstract class for overriding the default audio layer.

    The ChirpConnectSDK uses `sounddevice` to handle audio streams.
    If you need to provide your own audio layer then you should
    subclass this, and assign it to the `audio` attribute of
    the SDK before loading the config.

    The Audio layer must provide methods to start/stop the
    input/output streams. These will be called by SDK appropriately.

    Further documentation can be found in the Advanced section
    at https://developers.chirp.io/docs/getting-started/python
    """
    def __init__(self, sdk):
        pass

    def start(self, send=True, receive=True):
        """
        Start the audio engine.

        Args:
            send (bool): Enable output audio
            receive (bool): Enable input audio
        """
        pass

    def stop(self):
        """
        Stop the audio engine.
        """
        pass


class ChirpConnect(object):
    """
    The Chirp Python SDK.

    This is the main wrapper around the Chirp Connect Library.
    It exposes methods to send arbitrary payloads, and receive
    decoded chirps from the audio layer. Received data is handled
    in callback methods using the `CallbackSet`.

    A full getting started guide for the Chirp Python SDK can
    be found at https://developers.chirp.io/docs/getting-started/python

    You can set the SDK to run in debug mode by setting the flag true.
    This will write any input data from the microphone to a wav file
    called chirp_audio.wav.

    Args:
        key (str): Chirp application key
        secret (str): Chirp application secret
        config (str): Path to config file or config string
        debug (bool): Enter debug mode
        block (str): Select a different block from your ~/.chirprc other than [default]
    """
    def __init__(self, key=None, secret=None, config=None, debug=False, block=None):
        """
        Instantiate the SDK with an application key, secret, and config.
        These can be found at developers.chirp.io.
        If neither of these are specified, the credentials are attempted
        to be loaded from the ~/.chirprc file.
        """
        self.audio = None
        self.config = None
        self.debug = debug
        if key and secret:
            self.key = key.encode()
            self.secret = secret.encode()
        else:
            if block is None:
                block = 'default'
            self.read_chirprc(block)
        self._sdk = libconnect.new_chirp_connect(self.key, self.secret)
        self._uid = get_unique_id()
        self.callbacks = CallbackSet()
        self._callback_set = ChirpConnectCallbackSet(self)
        self._set_seed()
        if key and secret:
            if config:
                self.load_config(config) if os.path.exists(config) else self.set_config(config)
            else:
                self.set_config_from_network()
        else:
            self.set_config(self.config)
        if not self.is_offline:
            create_instantiate(self.key, self.secret, self._uid)

    def __del__(self):
        """
        Frees memory used by the Chirp Connect Library.

        Raises:
            ConnectError: If an error occurs when freeing memory.
        """
        if self._sdk:
            self._call(libconnect.del_chirp_connect, pointer(self._sdk))
            self._sdk = None

    def __str__(self):
        """
        Convenience method to output Chirp Connect Library version information.

        Returns:
            dict: Version information for the Chirp library.
        """
        return 'Chirp Connect {pyversion} [{cversion} {cbuild}] initialised.'.format(
            pyversion=__version__, cversion=self.version['version'], cbuild=self.version['build']
        )

    @property
    def version(self):
        """
        Get version information from the Chirp Connect Library.

        Returns:
            dict: Version information for Chirp libraries.
        """
        return {
            'name': libconnect.chirp_connect_get_library_name().decode(),
            'version': libconnect.chirp_connect_get_version().decode(),
            'build': libconnect.chirp_connect_get_build_number().decode()
        }

    def _call(self, fn, *args):
        """
        Internal method to make a call to C SDK functions that return
        an error code. If an error occurs, then get the associated
        error message and raise a ConnectError with it.

        Raises:
            ConnectError: If an error occurs.
        """
        rc = fn(*args)
        if rc != 0:
            err = libconnect.chirp_connect_error_code_to_string(rc)
            raise ConnectError(err.decode(), code=rc)

    # -- Getters & Setters

    def read_chirprc(self, block='default'):
        """
        Read the contents of the ~/.chirprc file to retrieve application
        key, secret and configuration.

        Args:
            block (str): The block name in ~/.chirprc to use

        Raises:
            IOError: If no ~/.chirprc file exists
            ValueError: If there is an error parsing the file
        """
        config = configparser.ConfigParser()
        rc = config.read(os.path.expanduser('~/.chirprc'))

        if rc:
            try:
                self.key = config.get(block, 'app_key').encode()
                self.secret = config.get(block, 'app_secret').encode()
                self.config = config.get(block, 'app_config')
            except configparser.NoSectionError:
                raise ValueError('Failed to parse ~/.chirprc. ' +
                    'Check you have a [{block}] section with an app_key, ' +
                    'app_secret and an app_config'.format(block=block))
        else:
            raise IOError('Could not find a ~/.chirprc file')


    def load_config(self, filename):
        """
        Load a config from file, and initialise the Chirp Connect Library.

        This must be done after immediately after instantiating the SDK.
        Unless you are implementing your own audio layer, then the audio
        attribute must be set first.

        Args:
            filename (str): The path to the config file

        Raises:
            ConnectError: If the config is invalid or there is an error
                setting the callbacks.
        """
        with open(filename, 'r') as config:
            self.set_config(config.read())

    def set_config(self, config):
        """
        Initialise the Chirp Connect Library with a config.

        This sets up the config and the internal callback set.
        If using the default sounddevice audio layer, then this is instantiated here.

        Args:
            config (str): config string

        Raises:
            ConnectError: If the config is invalid or there is an error setting
                the callbacks.
        """
        if not self.audio:
            self.audio = Audio(self)
        try:
            self._call(libconnect.chirp_connect_set_config, self._sdk, config.encode())
        except ConnectError as e:
            raise type(e)(str(e) + '\nEnsure you are passing in a valid config string or file path')

        self._call(libconnect.chirp_connect_set_callbacks, self._sdk, self._callback_set)
        self._max_payload_length = self.max_payload_length

    def set_config_from_network(self, name=None):
        """
        Retrieve a config for your application, and initialise the
        Chirp Connect Library. If no config name is specified, then
        the default config is used.

        Args:
            name (str): config name, default is used if not set

        Raises:
            ConnectNetworkError: If the request to retrieve the config fails.
            ConnectError: If the config is invalid or there is an error setting
            the callbacks.
        """
        config = get_config_from_network(self.key, self.secret, name)
        if config:
            self.set_config(config)

    def _set_seed(self, seed=None):
        """ Set the seed for the random generator """
        seed = randrange(2 ** 32 - 1) if seed is None else seed
        libconnect.chirp_connect_set_random_seed(self._sdk, seed)

    def set_callbacks(self, callbacks):
        """
        Set the callback set, used for consistency between platforms.

        Args:
            callbacks: (CallbackSet): Callback set

        Raises:
            ConnectError: If there is an error setting the callbacks.
        """
        self._call(libconnect.chirp_connect_set_callbacks, self._sdk, self._callback_set)
        self.callbacks = callbacks

    @property
    def is_offline(self):
        """
        bool: Returns true if configured in offline mode.
        """
        return libconnect.chirp_connect_is_offline_mode(self._sdk)

    @property
    def volume(self):
        """
        float: Property to get/set the SDK volume.
        """
        return round(libconnect.chirp_connect_get_volume(self._sdk), 2)

    @volume.setter
    def volume(self, level):
        libconnect.chirp_connect_set_volume(self._sdk, float(level))

    @property
    def input_sample_rate(self):
        """
        int: Property to get/set the SDK input sample rate.
        """
        rv = libconnect.chirp_connect_get_input_sample_rate(self._sdk)
        if rv == 0:
            raise ConnectError("Couldn't get input sample rate (is chirpsdk initialised?)")
        return rv

    @input_sample_rate.setter
    def input_sample_rate(self, rate):
        self._call(libconnect.chirp_connect_set_input_sample_rate, self._sdk, rate)

    @property
    def output_sample_rate(self):
        """
        int: Property to get/set the SDK output sample rate.
        """
        rv = libconnect.chirp_connect_get_output_sample_rate(self._sdk)
        if rv == 0:
            raise ConnectError("Couldn't get output sample rate (is chirpsdk initialised?)")
        return rv

    @output_sample_rate.setter
    def output_sample_rate(self, rate):
        self._call(libconnect.chirp_connect_set_output_sample_rate, self._sdk, rate)

    @property
    def state(self):
        """
        int: Property to get the current state of the SDK.

        Returns either
            chirpsdk.CHIRP_CONNECT_STATE_NOT_CREATED
            chirpsdk.CHIRP_CONNECT_STATE_STOPPED
            chirpsdk.CHIRP_CONNECT_STATE_PAUSED
            chirpsdk.CHIRP_CONNECT_STATE_RUNNING
            chirpsdk.CHIRP_CONNECT_STATE_SENDING
            chirpsdk.CHIRP_CONNECT_STATE_RECEIVING
        """
        return libconnect.chirp_connect_get_state(self._sdk)

    @property
    def auto_mute(self):
        """
        bool: Property to get/set the auto mute function of the SDK.

        Auto-mute prevents the SDK from hearing its own chirps when
        it is sending data. This should be True in almost all cases.
        """
        return libconnect.chirp_connect_get_auto_mute(self._sdk)

    @auto_mute.setter
    def auto_mute(self, mute):
        libconnect.chirp_connect_set_auto_mute(self._sdk, bool(mute))

    @property
    def protocol_name(self):
        """
        str: Property to get the configured protocol name.
        """
        return libconnect.chirp_connect_get_protocol_name(self._sdk).decode()

    @property
    def protocol_version(self):
        """
        int: Returns the current protocol version.
        """
        return libconnect.chirp_connect_get_protocol_version(self._sdk)

    @property
    def expiry(self):
        """
        datetime: Returns the expiry date of the current configuration.
        """
        dt = libconnect.chirp_connect_get_expiry_time(self._sdk)
        return datetime.utcfromtimestamp(dt)

    def get_duration(self, length):
        """
        float: Returns the duration of a chirp of `length` bytes in seconds.
        """
        return round(libconnect.chirp_connect_get_duration_for_payload_length(self._sdk, length), 3)

    @property
    def channel_count(self):
        """
        int: Returns the number of channels supported by the current configuration.
        """
        return libconnect.chirp_connect_get_channel_count(self._sdk)

    @property
    def transmission_channel(self):
        """
        int: Property to get/set the transmission channel on which data is sent.
        """
        return libconnect.chirp_connect_get_transmission_channel(self._sdk)

    @transmission_channel.setter
    def transmission_channel(self, channel):
        libconnect.chirp_connect_set_transmission_channel(self._sdk, int(channel))

    def get_state_for_channel(self, channel):
        """
        int: Property to get the current state of a channel.

        Returns either
            chirpsdk.CHIRP_CONNECT_STATE_NOT_CREATED
            chirpsdk.CHIRP_CONNECT_STATE_STOPPED
            chirpsdk.CHIRP_CONNECT_STATE_PAUSED
            chirpsdk.CHIRP_CONNECT_STATE_RUNNING
            chirpsdk.CHIRP_CONNECT_STATE_SENDING
            chirpsdk.CHIRP_CONNECT_STATE_RECEIVING
        """
        return libconnect.chirp_connect_get_state_for_channel(self._sdk, int(channel))

    # -- States

    def start(self, send=True, receive=True):
        """
        Start the SDK running.

        The SDK can be configured to run in send mode, receive mode
        or both. The default is send and receive mode.
        This also calls the `start` method in the audio layer.

        Args:
            send (bool): Enable send mode
            receive (bool): Enable receive mode

        Raises:
            ConnectError: If there is an error starting the
                Chirp Connect Library.
        """
        if self.audio:
            self.audio.start(send=send, receive=receive)
        self._call(libconnect.chirp_connect_start, self._sdk)

    def pause(self, state):
        """
        Pause the SDK and audio streams.

        Args:
            state (bool): True to pause, False to resume

        Raises:
            ConnectError: If there is an error pausing the
                Chirp Connect Library.
        """
        if self.audio:
            self.audio.stop() if state else self.audio.start()
        self._call(libconnect.chirp_connect_pause, self._sdk, bool(state))

    def stop(self):
        """
        Stop the SDK and audio streams.

        Raises:
            ConnectError: If there is an error stopping the
                Chirp Connect Library.
        """
        if self.audio:
            self.audio.stop()
        self._call(libconnect.chirp_connect_stop, self._sdk)

    # -- Callbacks

    def trigger_callbacks(self, payload):
        """
        Trigger the callback methods with a payload.

        Args:
            payload (bytearray): The data for the simulation.
        """
        data = (c_uint8 * len(payload))(*payload)
        libconnect.chirp_connect_trigger_callbacks(self._sdk, data, len(data))

    # -- Processing

    def process_input(self, input):
        """
        Process input data only. Used for receive only mode.

        An input array of floating-point audio samples should be passed in.
        The Chirp Connect Library will trigger the callback methods
        if any chirps are decoded. The input data must contain values
        ranging from -1 to +1, and must be sampled at the same rate as
        the SDK's input_sample_rate property.

        Args:
            input (bytes): The input audio data as a string of bytes.

        Raises:
            ConnectError: If there is an error processing the data.
        """
        if self._sdk is not None:
            length = int(len(input) / 4)
            floats = cast(input, POINTER(c_float))
            self._call(libconnect.chirp_connect_process_input, self._sdk, floats, length)

    def process_output(self, output):
        """
        Process output data only. Used for send only mode.

        An output array should be passed by reference.
        The Chirp Connect Library will populate the
        output buffer with any data to be sent. The data will
        be sampled at the SDK's output_sample_rate property.

        Args:
            output (buffer): The output buffer to be populated.

        Raises:
            ConnectError: If there is an error processing the data.
        """
        if self._sdk is not None:
            length = int(len(output) / 4)
            floats = cast(pointer(c_char.from_buffer(output, 0)), POINTER(c_float))
            self._call(libconnect.chirp_connect_process_output, self._sdk, floats, length)

    def process_shorts_input(self, input):
        """
        Process input data only. Used for receive only mode.

        An input array of 16bit signed integer audio samples should be passed in.
        The Chirp Connect Library will trigger the callback methods
        if any chirps are decoded. The input data must contain values
        ranging from -32767 to +32767, and must be sampled at the same rate as
        the SDK's input_sample_rate property.

        Args:
            input (bytes): The input audio data as a string of bytes.

        Raises:
            ConnectError: If there is an error processing the data.
        """
        if self._sdk is not None:
            length = int(len(input) / 2)
            shorts = cast(input, POINTER(c_short))
            self._call(libconnect.chirp_connect_process_shorts_input, self._sdk, shorts, length)

    def process_shorts_output(self, output):
        """
        Process output data only. Used for send only mode.

        An output array should be passed by reference.
        The Chirp Connect Library will populate the
        output buffer with any data to be sent. The data will
        be sampled at the SDK's output_sample_rate property.

        Args:
            output (buffer): The output buffer to be populated.

        Raises:
            ConnectError: If there is an error processing the data.
        """
        if self._sdk is not None:
            length = int(len(output) / 2)
            shorts = cast(pointer(c_char.from_buffer(output, 0)), POINTER(c_short))
            self._call(libconnect.chirp_connect_process_shorts_output, self._sdk, shorts, length)

    # -- Payload

    @property
    def max_payload_length(self):
        """
        int: Property to get the max payload length available with the current configuration.
        """
        return int(libconnect.chirp_connect_get_max_payload_length(self._sdk))

    def new_payload(self, data=None):
        """
        Generate an arbitrary Chirp Payload.
        A Chirp Payload is subclass of the built in type (bytearray).
        It will accept the same data types as a bytearray, ie. an integer,
        a string or an array of bytes.

        Args:
            data: The payload data

        Returns:
            payload (Payload): The Chirp Payload (bytearray)

        Raises:
            ValueError: If the data length is longer than the max payload length.
                This is set by the config. Or if there is no data.
        """
        data = [] if data is None else data
        if len(data) == 0:
            raise ValueError('Cannot generate a null payload')
        return _Payload(self, data)

    def random_payload(self, length=None):
        """
        Generate a random Chirp Payload of `length` bytes
        If no length is specified, then a payload of a random
        length (up to the max_payload_length) is generated.

        Args:
            length: The required length of the payload (optional)

        Returns:
            Payload: A Chirp Payload containing random data (bytearray)
        """
        length = 0 if length is None else length
        lenptr = pointer(c_size_t(length))
        data = libconnect.chirp_connect_random_payload(self._sdk, lenptr)
        payload = _Payload(self, data[:lenptr.contents.value])
        libconnect.chirp_connect_free(cast(data, c_void_p))
        return payload

    def is_valid(self, payload):
        """
        Check if a payload is valid.

        Args:
            payload (Payload): The Chirp Payload (bytearray)

        Returns:
            bool: True if valid.
        """
        data = (c_uint8 * len(payload))(*payload)
        rc = libconnect.chirp_connect_is_valid(self._sdk, data, len(data))
        return rc == 0

    def as_string(self, payload):
        """
        Returns the string representation of the Chirp Payload.

        Args:
            payload (Payload): The Chirp Payload (bytearray)

        Returns:
            str: The string representation of the Chirp Payload.
        """
        hexstring = ''
        data = (c_uint8 * len(payload))(*payload)
        cdata = libconnect.chirp_connect_as_string(self._sdk, data, len(payload))
        for i in range(len(payload) * 2):
            hexstring += cdata[i].decode()
        libconnect.chirp_connect_free(cast(cdata, c_void_p))
        return str(hexstring)

    def send(self, payload, blocking=False):
        """
        Send a Chirp Payload.
        This will pass the payload data to the Chirp Connect Library, which will then be
        processed into the output buffer in the `process` functions.
        The data will be transmitted asynchronously, unless the blocking flag
        is set to True.

        Args:
            payload (Payload): The Chirp Payload (bytearray)
            blocking (bool): True to block until send has completed

        Raises:
            RuntimeError: If sending was not enabled when starting the SDK.
            ConnectError: If there is an error sending the data.
        """
        if self.audio and self.audio.output_stream is None:
            raise RuntimeError('Sending data not enabled, set send to True when starting the SDK')

        data = (c_uint8 * len(payload))(*payload)
        self._call(libconnect.chirp_connect_send, self._sdk, data, len(data))
        if not self.is_offline:
            create_send(
                self.key, self.secret, self._uid, len(data),
                self.protocol_name, self.protocol_version)

        if blocking:
            delay = (self.audio.block_size / float(self.output_sample_rate) if
                     self.audio and self.audio.block_size else 0.1)
            while self.state == CHIRP_CONNECT_STATE_SENDING:
                time.sleep(delay)
            time.sleep(delay)
