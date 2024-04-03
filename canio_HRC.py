import can
import bitstring
from bitarray.util import ba2int
from bitarray import bitarray
import time
import struct
from lint import docstring
import config_HRC as HRC

################################################################################
################################### Can Send ###################################
################################################################################

def isfloat(x):
    try:
        a = float(x)
    except (TypeError, ValueError):
        return False
    else:
        return True

def isint(x):
    try:
        a = float(x)
        b = int(a)
    except (TypeError, ValueError):
        return False
    else:
        return a == b

def intTypeCheck(var, type, label, size):
    num = var.get()

    buffer = {
        int:   ( isint,   lambda val: dict(int=val),  "Integer Number" ),
        float: ( isfloat, lambda val: dict(float=val), "Decimal Value" )
    }

    if type not in buffer:
        return False
    
    check, bitarrArg, errString = buffer[type]
    
    try:
        if not check(num):
            label.config(text="Invalid Type.\n%s is required as Input"%errString, fg="red")
            return False
        
        binstr = bitstring.BitArray(length=size, **bitarrArg(type(num))).bin
        label.config(text="Command Sent!", fg="green")
        return True
    except bitstring.CreationError as e:
        label.config(text=e, fg="red")
        return False

class CanSend:
    def __init__(self, **busargs):
        print("Hericlitus Rocket Controller CanSend instance created")
        self.bus = can.interface.Bus(**busargs)

    def send(self, ID, DATA, prefix=""):
        print(">>", prefix, ID, DATA)
        msg = can.Message(arbitration_id=ID, data=DATA, is_extended_id=False)
        self.bus.send(msg)

    def __call__(self, ID, DATA):
        self.send(ID, DATA)

    ##############################
    ########## Generics ##########
    ##############################
    #     These functions are    #
    # commonly used throughout   #
    # the rest of CanSend. All   #
    # other functions are for    #
    # your convinience, and      #
    # derive from these.         #
    
    @docstring("""
    # Sets the timing for the target id.
    # 
    # Arguments:
    # id: Message id -- Setters in range [32, 36].
    # time_micros: unsigned 40 bit integer??? -- in microseconds from ???
    """)
    def set_timing(self, id, time_micros):
        binstr = bitstring.BitArray(int=time_micros, length=40).bin
        data = [binstr[i:i+8] for i in range(0, len(binstr), 8)]
        self.send(id, data, "Sent Timer Message:")

    @docstring("""
    # Sends a unary message.
    # 
    # Arguments:
    # id: Command id -- Defined in Config.h
    """)
    def send_unary_message(self, id):
        self.send(id, [], "Sent Unary Message:")
        

    ##############################
    ###### Vehicle Commands ######
    ##############################
        
    @docstring("""
    # Sends the abort command.
    """)
    def abort(self):
        self.send_unary_message(HRC.ABORT)

    @docstring("""
    # Sends the vent command.
    """)
    def vent(self):
        self.send_unary_message(HRC.VENT)

    @docstring("""
    # Sends the fire command.
    """)
    def fire(self):
        self.send_unary_message(HRC.FIRE)

    @docstring("""
    # Sends the tank pressurize command.
    """)
    def tank_press(self):
        self.send_unary_message(HRC.TANK_PRESS)

    @docstring("""
    # Sends the high press pressurize command.
    """)
    def high_press(self):
        self.send_unary_message(HRC.HIGH_PRESS)

    @docstring("""
    # Sends the standby command.
    """)
    def standby(self):
        self.send_unary_message(HRC.STANDBY)

    @docstring("""
    # Sends the passive command.
    """)
    def passive(self):
        self.send_unary_message(HRC.PASSIVE)

    @docstring("""
    # Sends the test command.
    """)
    def test(self):
        self.send_unary_message(HRC.TEST)

    ##############################
    ##### Valves & Igniters ######
    ##############################
        
    @docstring("""
    # Sets Igniter 1 to off.
    """)
    def ign1_off(self):
        self.send_unary_message(HRC.IGN1_OFF)


    @docstring("""
    # Sets Igniter 1 to on.
    """)
    def ign1_on(self):
        self.send_unary_message(HRC.IGN1_ON)


    @docstring("""
    # Sets Igniter 2 to off.
    """)
    def ign2_off(self):
        self.send_unary_message(HRC.IGN2_OFF)


    @docstring("""
    # Sets Igniter 2 to on.
    """)
    def ign2_on(self):
        self.send_unary_message(HRC.IGN2_ON)


    @docstring("""
    # Sets High Pressure Vent to close.
    """)
    def hv_close(self):
        self.send_unary_message(HRC.HV_CLOSE)


    @docstring("""
    # Sets High Pressure Vent open.
    """)
    def hv_open(self):
        self.send_unary_message(HRC.HV_OPEN)


    @docstring("""
    # Sets High Pressure to close.
    """)
    def hp_close(self):
        self.send_unary_message(HRC.HP_CLOSE)


    @docstring("""
    # Sets High Pressure to open.
    """)
    def hp_open(self):
        self.send_unary_message(HRC.HP_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Dome Vent to close.
    """)
    def ldv_close(self):
        self.send_unary_message(HRC.LDV_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Dome Vent to open.
    """)
    def ldv_open(self):
        self.send_unary_message(HRC.LDV_OPEN)


    @docstring("""
    # Sets Fuel Dome Vent to close.
    """)
    def fdv_close(self):
        self.send_unary_message(HRC.FDV_CLOSE)


    @docstring("""
    # Sets Fuel Dome Vent to open.
    """)
    def fdv_open(self):
        self.send_unary_message(HRC.FDV_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Dome Regulator to close.
    """)
    def ldr_close(self):
        self.send_unary_message(HRC.LDR_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Dome Regulator to open.
    """)
    def ldr_open(self):
        self.send_unary_message(HRC.LDR_OPEN)


    @docstring("""
    # Sets Fuel Dome Regulator to close.
    """)
    def fdr_close(self):
        self.send_unary_message(HRC.FDR_CLOSE)


    @docstring("""
    # Sets Fuel Dome Regulator to open.
    """)
    def fdr_open(self):
        self.send_unary_message(HRC.FDR_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Vent to close.
    """)
    def lv_close(self):
        self.send_unary_message(HRC.LV_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Vent to open.
    """)
    def lv_open(self):
        self.send_unary_message(HRC.LV_OPEN)


    @docstring("""
    # Sets Fuel Vent to close.
    """)
    def fv_close(self):
        self.send_unary_message(HRC.FV_CLOSE)


    @docstring("""
    # Sets Fuel Vent to open.
    """)
    def fv_open(self):
        self.send_unary_message(HRC.FV_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Main Valve to close.
    """)
    def lmv_close(self):
        self.send_unary_message(HRC.LMV_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Main Valve to open.
    """)
    def lmv_open(self):
        self.send_unary_message(HRC.LMV_OPEN)


    @docstring("""
    # Sets Fuel Main Valve to close.
    """)
    def fmv_close(self):
        self.send_unary_message(HRC.FMV_CLOSE)


    @docstring("""
    # Sets Fuel Main Valve to open.
    """)
    def fmv_open(self):
        self.send_unary_message(HRC.FMV_OPEN)

    ##############################
    ########### Timing ###########
    ##############################

    @docstring("""
    # Sets the ignition time for both igniters.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_ignition(self, time_micros):
        self.set_timing(HRC.SET_IGNITION, time_micros)

    @docstring("""
    # Sets the opening time for the liquid oxygen main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_lmv_open(self, time_micros):
        self.set_timing(HRC.SET_LMV_OPEN, time_micros)

    @docstring("""
    # Sets the opening time for the fuel main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_fmv_open(self, time_micros):
        self.set_timing(HRC.SET_FMV_OPEN, time_micros)

    @docstring("""
    # Sets the closing time for the liquid oxygen main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_lmv_close(self, time_micros):
        self.set_timing(HRC.SET_LMV_CLOSE, time_micros)

    @docstring("""
    # Sets the closing time for the fuel main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_fmv_close(self, time_micros):
        self.set_timing(HRC.SET_FMV_CLOSE, time_micros)

    ##############################
    ####### Miscellaneous ########
    ##############################
        
    @docstring("""
    # Pings the rocket.
    """)
    def ping(self):
        self.send_unary_message(HRC.PING_PI_ROCKET)

    @docstring("""
    # Zeros the pressure transducers.
    """)
    def zero_pts(self):
        self.send_unary_message(HRC.ZERO_PTS)

################################################################################
################################# Can Receive ##################################
################################################################################

class CanReceive:

    def __init__(self, **busargs):
        print("Hericlitus Rocket Controller CanReceive instance created")
        self.bus = can.interface.Bus(**busargs)

        self.States = {k:v['states'][0] for k,v in HRC.ToggleLUT.items()}
        self.Sensor_Raw = {k:0 for k,v in HRC.SensorLUT.items()}
        self.Sensor_Val = {k:v['b'] for k,v in HRC.SensorLUT.items()}

        self.rocketState = {k:HRC.PASSIVE for k in HRC.ToggleKeys.keys()}
        self.time_micros = {k:-1 for k in HRC.ToggleKeys.keys()}

    @docstring("""
    Runs the CanReceive thread.
    """)
    def run(self):
        self.loop = True

        for cycle in self.generator():
            self.loop = cycle

    @docstring("""
    Returns a generator that runs a single message loop cycle.
    """)
    def generator(self):
        while self.loop:
            msg_in = self.bus.recv(timeout=None)
            try:
                yield self.translateMessage(*self.parseMessage(msg_in))
            except Exception as e:
                print(e)
            

    @docstring("""
    # Parses a message recieved by the Can Bus.
    # Returns message id as an integer, and the data in hex and binary formats.
    # 
    # Arguments:
    # msg_in: Can message
    """)
    def parseMessage(self, msg_in):
        # Grabs Message ID
        msg_id = int(msg_in.arbitration_id)
        
        # Grabs the data in the msg
        data_list_hex = msg_in.data.hex()
        data_bin = bitstring.BitArray(hex=data_list_hex).bin
        
        return msg_id, data_list_hex, data_bin
    
    @docstring("""
    # Passes the parsed message to the appropriate decoder.
    """)
    def translateMessage(self, msg_id, data_list_hex, data_bin):

        if msg_id in HRC.ToggleKeys:
            return self.recvStateReport(msg_id, data_list_hex, data_bin)
        
        if msg_id in HRC.SensorKeys:
            return self.recvSensorData(msg_id, data_list_hex, data_bin)
        
        # DEBUG
        #for state_id, lut in HRC.ToggleLUT.items():
        #    if msg_id in lut['states']:
        #        time.sleep(1)
        #        s = self.States[state_id]
        #        self.States[state_id] = msg_id
        #        raise KeyError("Recieved msg with id: %s, altering %s"%(msg_id, s))
        #        return 

        raise KeyError("Unknown message recieved with id: %d, and data [%s]"%(msg_id, str(data_list_hex)))

    @docstring("""
    # State report
    """)
    def recvStateReport(self, msg_id, data_list_hex, data_bin):

        self.time_micros[msg_id] = int('0'+data_bin[:32], base=2)
        self.rocketState[msg_id] = int('0'+data_list_hex[4], base=16)

        state_bits = '{0:06b}'.format(int('0'+data_list_hex[5], base=16))
        states = list(map(lambda b: int('0'+b, base=2), state_bits))

        for key, state in zip(HRC.ToggleKeys[msg_id], states):
            self.States[key] = HRC.ToggleLUT[key]['states'][state]

    @docstring("""
    # Sensor data
    """)
    def recvSensorData(self, msg_id, data_list_hex, data_bin):

        vals = [int('0'+data_bin[i:i+16], base=2) for i in range(0, 64, 16)]

        for key, val in zip(HRC.SensorKeys[msg_id], vals):
            if key not in HRC.SensorLUT:
                continue
            
            v = val / HRC.SENSOR_MULTIPLIER
            self.Sensor_Raw[key] = v
            self.Sensor_Val[key] = HRC.SensorLUT[key]['b'] + HRC.SensorLUT[key]['m'] * v
