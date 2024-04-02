import can
import bitstring
from bitarray.util import ba2int
from bitarray import bitarray
import time
import struct
from lint import docstring

NODEID = 8
VERIFICATIONID = 166
SENSOR_MULTIPLIER = 100

################################################################################
############## HeraclitusRocketController / Config.h Definitions ###############
################################################################################

# Valves & Igniters
NUM_VALVES   = 10
NUM_IGNITERS = 2

# Vehicle Commands
ABORT        = 0
VENT         = 1
FIRE         = 2
TANK_PRESS   = 3
HIGH_PRESS   = 4
STANDBY      = 5
PASSIVE      = 6
TEST         = 7

# Valve & Igniter (HPO Commands)
IGN1_OFF     = 8   # Igniter One
IGN1_ON      = 9

IGN2_OFF     = 10  # Igniter Two
IGN2_ON      = 11

HV_CLOSE     = 12  # High Vent valve
HV_OPEN      = 13

HP_CLOSE     = 14  # High Press valve
HP_OPEN      = 15

LDV_CLOSE    = 16  # Lox Dome Vent valve
LDV_OPEN     = 17

FDV_CLOSE    = 18  # Fuel Dome Vent valve
FDV_OPEN     = 19

LDR_CLOSE    = 20  # Lox Dome Reg valve
LDR_OPEN     = 21

FDR_CLOSE    = 22  # Fuel Dome Reg valve
FDR_OPEN     = 23

LV_CLOSE     = 24  # Lox Vent valve
LV_OPEN      = 25

FV_CLOSE     = 26  # Fuel Vent valve
FV_OPEN      = 27

LMV_CLOSE    = 28  # Lox Main valve
LMV_OPEN     = 29

FMV_CLOSE    = 30  # Fuel Main valve
FMV_OPEN     = 31

# Timing
SET_IGNITION  = 32  # Set ignition time for both igniters.
SET_LMV_OPEN  = 33  # Set LMV open time.
SET_FMV_OPEN  = 34  # Set FMV open time. 
SET_LMV_CLOSE = 35  # Set LMV close time.
SET_FMV_CLOSE = 36  # Set FMV close time.

GET_IGNITION  = 37  # Confirm ignition time for both igniters.
GET_LMV_OPEN  = 38  # Confirm LMV open time.
GET_FMV_OPEN  = 39  # Confirm FMV open time.
GET_LMV_CLOSE = 40  # Confirm LMV close time.
GET_FMV_CLOSE = 41  # Confirm FMV close time.

# Ping
PING_PI_ROCKET = 42  # *Important*: Pi Box sends a ping to the rocket. 
PING_ROCKET_PI = 43  # Rocket sends a ping to the Pi Box.

# PT Configuration
ZERO_PTS = 44  # Zero the pressure transducers.

# State Reports
SR_PROP   = 127
SR_ENGINE = 128

# Sensor Reports
SENS_1_4_PROP     = 129 # Lox High,   Fuel High, Lox Dome,   Fuel Dome
SENS_5_8_PROP     = 130 # Lox Tank1,  Lox Tank2, Fuel Tank1, Fuel Tank2
SENS_9_12_ENGINE  = 131 # Pneumatics, Lox Inlet, Fuel Inlet, Fuel Injector
SENS_13_16_ENGINE = 132 # Chamber1,   Chamber2,  UNUSED,     UNUSED

# Data Direction Inputs 
INPUT  = 0
OUTPUT = 1

# Igniter Digital Pin Designations and IDs | ALARA LOWER 

IGN1_ID      = 10  # Igniter A / ENG-IGNA / ALARA Lower
IGN1_PIN_DIG = 83  #ALARA: DIG5 | Teensy 3.6 MCU Pin: PTC16
IGN1_PIN_PWM = 2 


IGN2_ID      = 11  # Igniter B / ENG-IGNB
IGN2_PIN_DIG = 81  # ALARA: DIG5 | Teensy 3.6 MCU Pin: PTC14
IGN2_PIN_PWM = 10  # In Dan's Code they are both 2?  
      

# Valve Digital Pin Designations and IDs | ALARA LOWER 

HP_ID        = 20  # High Press valve / SV HI PRES  
HP_PIN_DIG   = 87  # ALARA: DIG1 | Teensy 3.6 MCU Pin: PTD10
HP_PIN_PWM   = 5

HV_ID        = 21  # High Vent valve / SV HI PRES V 
HV_PIN_DIG   = 86  # ALARA: DIG2 | Teensy 3.6 MCU Pin: PTC19
HV_PIN_PWM   = 6

FMV_ID       = 22  # Fuel Main valve / SV MV FUEL 
FMV_PIN_DIG  = 85  # ALARA: DIG3 | Teensy 3.6 MCU Pin: PTC18
FMV_PIN_PWM  = 8  

LMV_ID       = 23  # Lox Main valve / SV MV LOX
LMV_PIN_DIG  = 84  # ALARA: DIG4 | Teensy 3.6 MCU Pin: PTC17
LMV_PIN_PWM  = 7

# Valve Digital Pin Designations and IDs | ALARA UPPER 

LV_ID        = 24  # Lox Vent valve / SV LOX V
LV_PIN_DIG   = 87  # ALARA: DIG1 | Teensy 3.6 MCU Pin: PTD10
LV_PIN_PWM   = 5

LDV_ID       = 25  # Lox Dome Vent valve / SV DREG L
LDV_PIN_DIG  = 85  # ALARA: DIG3 | Teensy 3.6 MCU Pin: PTC18
LDV_PIN_PWM  = 8

LDR_ID       = 26  # Lox Dome Reg valve / SV DREG LV
LDR_PIN_DIG  = 84  # ALARA: DIG4 | Teensy 3.6 MCU Pin: PTC17
LDR_PIN_PWM  = 7

FV_ID        = 27  # Fuel Vent valve / SV FUEL V 
FV_PIN_DIG   = 83  # ALARA: DIG5 | Teensy 3.6 MCU Pin: PTC16
FV_PIN_PWM   = 2

FDV_ID       = 28  # Fuel Dome Vent valve / SV DREG F V 
FDV_PIN_DIG  = 81  # ALARA: DIG7 | Teensy 3.6 MCU Pin: PTC14
FDV_PIN_PWM  = 10

FDR_ID       = 29  # Fuel Dome Reg valve /  SV DREG F
FDR_PIN_DIG  = 80  # ALARA: DIG8 | Teensy 3.6 MCU Pin: PTC13
FDR_PIN_PWM  = 9



# Pressure Transducer Sesnor Pin Designations, IDs, and Calibration Values
# (sensors are currently uncalibrated)

#Upper Prop Node:
PT_LOX_HIGH_ID         = (1<<0)  #00000000 00000001  Upper A22
PT_LOX_HIGH_PIN        = "A22"
PT_LOX_HIGH_CAL_M      = 1.0
PT_LOX_HIGH_CAL_B      = 0.0

PT_FUEL_HIGH_ID        = (1<<1)  #00000000 00000010  Upper A21
PT_FUEL_HIGH_PIN       = "A21"
PT_FUEL_HIGH_CAL_M     = 1.0
PT_FUEL_HIGH_CAL_B     = 0.0

PT_LOX_DOME_ID         = (1<<2)  #00000000 00000100  Upper  A3
PT_LOX_DOME_PIN        = "A3"
PT_LOX_DOME_CAL_M      = 1.0
PT_LOX_DOME_CAL_B      = 0.0

PT_FUEL_DOME_ID        = (1<<3)  #00000000 00001000  Upper  A2
PT_FUEL_DOME_PIN       = "A2"
PT_FUEL_DOME_CAL_M     = 1.0
PT_FUEL_DOME_CAL_B     = 0.0

PT_LOX_TANK_1_ID       = (1<<4)  #00000000 00010000  Upper A14
PT_LOX_TANK_1_PIN      = "A14"
PT_LOX_TANK_1_CAL_M    = 1.0
PT_LOX_TANK_1_CAL_B    = 0.0

PT_LOX_TANK_2_ID       = (1<<5)  #00000000 00100000  Upper A11
PT_LOX_TANK_2_PIN      = "A11"
PT_LOX_TANK_2_CAL_M    = 1.0
PT_LOX_TANK_2_CAL_B    = 0.0

PT_FUEL_TANK_1_ID      = (1<<6)  #00000000 01000000  Upper A15
PT_FUEL_TANK_1_PIN     = "A15"
PT_FUEL_TANK_1_CAL_M   = 1.0
PT_FUEL_TANK_1_CAL_B   = 0.0

PT_FUEL_TANK_2_ID      = (1<<7)  #00000000 10000000  Upper A10
PT_FUEL_TANK_2_PIN     = "A10"
PT_FUEL_TANK_2_CAL_M   = 1.0
PT_FUEL_TANK_2_CAL_B   = 0.0

#Lower Engine Node:
PT_PNUEMATICS_ID       = (1<<8)  #00000001 00000000  Lower A15
PT_PNUEMATICS_PIN      = "A15"
PT_PNUEMATICS_CAL_M    = 1.0
PT_PNUEMATICS_CAL_B    = 0.0

PT_LOX_INLET_ID        = (1<<9)  #00000010 00000000  Lower A21
PT_LOX_INLET_PIN       = "A21"
PT_LOX_INLET_CAL_M     = 1.0
PT_LOX_INLET_CAL_B     = 0.0

PT_FUEL_INLET_ID       = (1<<10) #00000100 00000000  Lower A22
PT_FUEL_INLET_PIN      = "A22"
PT_FUEL_INLET_CAL_M    = 1.0
PT_FUEL_INLET_CAL_B    = 0.0

PT_FUEL_INJECTOR_ID    = (1<<11) #00001000 00000000  Lower A14
PT_FUEL_INJECTOR_PIN   = "A14"
PT_FUEL_INJECTOR_CAL_M = 1.0
PT_FUEL_INJECTOR_CAL_B = 0.0

PT_CHAMBER_1_ID        = (1<<12) #00010000 00000000  Lower A10
PT_CHAMBER_1_PIN       = "A10"
PT_CHAMBER_1_CAL_M     = 1.0
PT_CHAMBER_1_CAL_B     = 0.0

PT_CHAMBER_2_ID        = (1<<13) #00100000 00000000  Lower A11
PT_CHAMBER_2_PIN       = "A11"
PT_CHAMBER_2_CAL_M     = 1.0
PT_CHAMBER_2_CAL_B     = 0.0

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

    def send(self, ID, DATA):
        print(DATA)
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
        self.send(id, data)

    @docstring("""
    # Sends a unary message.
    # 
    # Arguments:
    # id: Command id -- Defined in Config.h
    """)
    def send_unary_message(self, id):
        self.send(id, [])

    ##############################
    ###### Vehicle Commands ######
    ##############################
        
    @docstring("""
    # Sends the abort command.
    """)
    def abort(self):
        self.send_unary_message(ABORT)

    @docstring("""
    # Sends the vent command.
    """)
    def vent(self):
        self.send_unary_message(VENT)

    @docstring("""
    # Sends the fire command.
    """)
    def fire(self):
        self.send_unary_message(FIRE)

    @docstring("""
    # Sends the tank pressurize command.
    """)
    def tank_press(self):
        self.send_unary_message(TANK_PRESS)

    @docstring("""
    # Sends the high press pressurize command.
    """)
    def high_press(self):
        self.send_unary_message(HIGH_PRESS)

    @docstring("""
    # Sends the standby command.
    """)
    def standby(self):
        self.send_unary_message(STANDBY)

    @docstring("""
    # Sends the passive command.
    """)
    def passive(self):
        self.send_unary_message(PASSIVE)

    @docstring("""
    # Sends the test command.
    """)
    def test(self):
        self.send_unary_message(TEST)

    ##############################
    ##### Valves & Igniters ######
    ##############################
        
    @docstring("""
    # Sets Igniter 1 to off.
    """)
    def ign1_off(self):
        self.send_unary_message(IGN1_OFF)


    @docstring("""
    # Sets Igniter 1 to on.
    """)
    def ign1_on(self):
        self.send_unary_message(IGN1_ON)


    @docstring("""
    # Sets Igniter 2 to off.
    """)
    def ign2_off(self):
        self.send_unary_message(IGN2_OFF)


    @docstring("""
    # Sets Igniter 2 to on.
    """)
    def ign2_on(self):
        self.send_unary_message(IGN2_ON)


    @docstring("""
    # Sets High Pressure Vent to close.
    """)
    def hv_close(self):
        self.send_unary_message(HV_CLOSE)


    @docstring("""
    # Sets High Pressure Vent open.
    """)
    def hv_open(self):
        self.send_unary_message(HV_OPEN)


    @docstring("""
    # Sets High Pressure to close.
    """)
    def hp_close(self):
        self.send_unary_message(HP_CLOSE)


    @docstring("""
    # Sets High Pressure to open.
    """)
    def hp_open(self):
        self.send_unary_message(HP_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Dome Vent to close.
    """)
    def ldv_close(self):
        self.send_unary_message(LDV_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Dome Vent to open.
    """)
    def ldv_open(self):
        self.send_unary_message(LDV_OPEN)


    @docstring("""
    # Sets Fuel Dome Vent to close.
    """)
    def fdv_close(self):
        self.send_unary_message(FDV_CLOSE)


    @docstring("""
    # Sets Fuel Dome Vent to open.
    """)
    def fdv_open(self):
        self.send_unary_message(FDV_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Dome Regulator to close.
    """)
    def ldr_close(self):
        self.send_unary_message(LDR_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Dome Regulator to open.
    """)
    def ldr_open(self):
        self.send_unary_message(LDR_OPEN)


    @docstring("""
    # Sets Fuel Dome Regulator to close.
    """)
    def fdr_close(self):
        self.send_unary_message(FDR_CLOSE)


    @docstring("""
    # Sets Fuel Dome Regulator to open.
    """)
    def fdr_open(self):
        self.send_unary_message(FDR_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Vent to close.
    """)
    def lv_close(self):
        self.send_unary_message(LV_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Vent to open.
    """)
    def lv_open(self):
        self.send_unary_message(LV_OPEN)


    @docstring("""
    # Sets Fuel Vent to close.
    """)
    def fv_close(self):
        self.send_unary_message(FV_CLOSE)


    @docstring("""
    # Sets Fuel Vent to open.
    """)
    def fv_open(self):
        self.send_unary_message(FV_OPEN)


    @docstring("""
    # Sets Liquid Oxygen Main Valve to close.
    """)
    def lmv_close(self):
        self.send_unary_message(LMV_CLOSE)


    @docstring("""
    # Sets Liquid Oxygen Main Valve to open.
    """)
    def lmv_open(self):
        self.send_unary_message(LMV_OPEN)


    @docstring("""
    # Sets Fuel Main Valve to close.
    """)
    def fmv_close(self):
        self.send_unary_message(FMV_CLOSE)


    @docstring("""
    # Sets Fuel Main Valve to open.
    """)
    def fmv_open(self):
        self.send_unary_message(FMV_OPEN)

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
        self.set_timing(SET_IGNITION, time_micros)

    @docstring("""
    # Sets the opening time for the liquid oxygen main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_lmv_open(self, time_micros):
        self.set_timing(SET_LMV_OPEN, time_micros)

    @docstring("""
    # Sets the opening time for the fuel main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_fmv_open(self, time_micros):
        self.set_timing(SET_FMV_OPEN, time_micros)

    @docstring("""
    # Sets the closing time for the liquid oxygen main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_lmv_close(self, time_micros):
        self.set_timing(SET_LMV_CLOSE, time_micros)

    @docstring("""
    # Sets the closing time for the fuel main valve.
    # 
    # Arguments:
    # time_micros: unsigned 40 bit integer???, in microseconds from ???
    """)
    def set_fmv_close(self, time_micros):
        self.set_timing(SET_FMV_CLOSE, time_micros)

    ##############################
    ####### Miscellaneous ########
    ##############################
        
    @docstring("""
    # Pings the rocket.
    """)
    def ping(self):
        self.send_unary_message(PING_PI_ROCKET)

    @docstring("""
    # Zeros the pressure transducers.
    """)
    def zero_pts(self):
        self.send_unary_message(ZERO_PTS)

################################################################################
################################# Can Receive ##################################
################################################################################

class CanReceive:
    
    StateLUT = {
        IGN1_ID : [ IGN1_OFF,  IGN1_ON],
        IGN2_ID : [ IGN2_OFF,  IGN2_ON],
        HP_ID   : [ HP_CLOSE,  HP_OPEN],
        HV_ID   : [ HV_CLOSE,  HV_OPEN],
        FMV_ID  : [FMV_CLOSE, FMV_OPEN],
        LMV_ID  : [LMV_CLOSE, LMV_OPEN],
        LV_ID   : [ LV_CLOSE,  LV_OPEN],
        LDV_ID  : [LDV_CLOSE, LDV_OPEN],
        LDR_ID  : [LDR_CLOSE, LDR_OPEN],
        FV_ID   : [ FV_CLOSE,  FV_OPEN],
        FDV_ID  : [FDV_CLOSE, FDV_OPEN],
        FDR_ID  : [FDR_CLOSE, FDR_OPEN],
    }

    StateKeys = {
        SR_ENGINE:[HP_ID,  HV_ID, FMV_ID, LMV_ID, IGN1_ID, IGN2_ID],
        SR_PROP:  [LV_ID, LDV_ID, LDR_ID,  FV_ID,  FDV_ID,  FDR_ID]
    }

    SensorLUT = {
        PT_LOX_HIGH_ID      : dict(pin=PT_LOX_HIGH_PIN,      m=PT_LOX_HIGH_CAL_M,      b=PT_LOX_HIGH_CAL_B),
        PT_FUEL_HIGH_ID     : dict(pin=PT_FUEL_HIGH_PIN,     m=PT_FUEL_HIGH_CAL_M,     b=PT_FUEL_HIGH_CAL_B),
        PT_LOX_DOME_ID      : dict(pin=PT_LOX_DOME_PIN,      m=PT_LOX_DOME_CAL_M,      b=PT_LOX_DOME_CAL_B),
        PT_FUEL_DOME_ID     : dict(pin=PT_FUEL_DOME_PIN,     m=PT_FUEL_DOME_CAL_M,     b=PT_FUEL_DOME_CAL_B),
        PT_LOX_TANK_1_ID    : dict(pin=PT_LOX_TANK_1_PIN,    m=PT_LOX_TANK_1_CAL_M,    b=PT_LOX_TANK_1_CAL_B),
        PT_LOX_TANK_2_ID    : dict(pin=PT_LOX_TANK_2_PIN,    m=PT_LOX_TANK_2_CAL_M,    b=PT_LOX_TANK_2_CAL_B),
        PT_FUEL_TANK_1_ID   : dict(pin=PT_FUEL_TANK_1_PIN,   m=PT_FUEL_TANK_1_CAL_M,   b=PT_FUEL_TANK_1_CAL_B),
        PT_FUEL_TANK_2_ID   : dict(pin=PT_FUEL_TANK_2_PIN,   m=PT_FUEL_TANK_2_CAL_M,   b=PT_FUEL_TANK_2_CAL_B),
        PT_PNUEMATICS_ID    : dict(pin=PT_PNUEMATICS_PIN,    m=PT_PNUEMATICS_CAL_M,    b=PT_PNUEMATICS_CAL_B),
        PT_LOX_INLET_ID     : dict(pin=PT_LOX_INLET_PIN,     m=PT_LOX_INLET_CAL_M,     b=PT_LOX_INLET_CAL_B),
        PT_FUEL_INLET_ID    : dict(pin=PT_FUEL_INLET_PIN,    m=PT_FUEL_INLET_CAL_M,    b=PT_FUEL_INLET_CAL_B),
        PT_FUEL_INJECTOR_ID : dict(pin=PT_FUEL_INJECTOR_PIN, m=PT_FUEL_INJECTOR_CAL_M, b=PT_FUEL_INJECTOR_CAL_B),
        PT_CHAMBER_1_ID     : dict(pin=PT_CHAMBER_1_PIN,     m=PT_CHAMBER_1_CAL_M,     b=PT_CHAMBER_1_CAL_B),
        PT_CHAMBER_2_ID     : dict(pin=PT_CHAMBER_2_PIN,     m=PT_CHAMBER_2_CAL_M,     b=PT_CHAMBER_2_CAL_B),
                         -1 : dict(pin=-1,                   m=1,                      b=0), # Padding
    }

    SensorKeys = {
        SENS_1_4_PROP:     [PT_LOX_HIGH_ID,   PT_FUEL_HIGH_ID,  PT_LOX_DOME_ID,    PT_FUEL_DOME_ID],
        SENS_5_8_PROP:     [PT_LOX_TANK_1_ID, PT_LOX_TANK_2_ID, PT_FUEL_TANK_1_ID, PT_FUEL_TANK_2_ID],
        SENS_9_12_ENGINE:  [PT_PNUEMATICS_ID, PT_LOX_INLET_ID,  PT_FUEL_INLET_ID,  PT_FUEL_INJECTOR_ID],
        SENS_13_16_ENGINE: [PT_CHAMBER_1_ID,  PT_CHAMBER_2_ID,  -1,                -1]
    }

    def __init__(self, **busargs):
        print("Hericlitus Rocket Controller CanReceive instance created")
        self.bus = can.interface.Bus(**busargs)

        self.States = {k:v[0] for k,v in self.StateLUT.items()}
        self.Sensor_Raw = {k:0 for k,v in self.SensorLUT.items()}
        self.Sensor_Val = {k:v['b'] for k,v in self.SensorLUT.items()}

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

        if msg_id in self.StateKeys:
            return self.recvStateReport(msg_id, data_list_hex, data_bin)
        
        if msg_id in self.SensorKeys:
            return self.recvSensorData(msg_id, data_list_hex, data_bin)
        
        raise KeyError("Unknown message recieved with id: %d, and data [%s]"%(msg_id, str(data_list_hex)))

    @docstring("""
    # State report
    """)
    def recvStateReport(self, msg_id, data_list_hex, data_bin):

        self.time_micros = int('0'+data_bin[:32], base=2)
        self.rocketState = int('0'+data_list_hex[4], base=16)

        state_bits = '{0:06b}'.format(int('0'+data_list_hex[5], base=16))
        states = list(map(lambda b: int('0'+b, base=2), state_bits))

        for key, state in zip(self.StateKeys[msg_id], states):
            self.States[key] = self.StateLUT[key][state]

    @docstring("""
    # Sensor data
    """)
    def recvSensorData(self, msg_id, data_list_hex, data_bin):

        vals = [int('0'+data_bin[i:i+16], base=2) for i in range(0, 64, 16)]

        for key, val in zip(self.SensorKeys[msg_id], vals):
            v = val / SENSOR_MULTIPLIER
            self.Sensor_Raw[key] = v
            self.Sensor_Val[key] = self.SensorLUT[key]['b'] + self.SensorLUT[key]['m'] * v
