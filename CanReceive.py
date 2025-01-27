import can
import bitstring
from bitarray.util import ba2int
from bitarray import bitarray
import time
import struct

NODEID = 8
VERIFICATIONID = 166

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
        print("RocketDriver2 CanSend instance created")
        self.bus = can.interface.Bus(**busargs)

    def send(self, ID, DATA):
        print(DATA)
        msg = can.Message(arbitration_id=ID, data=DATA, is_extended_id=False)
        self.bus.send(msg)

    def __call__(self, ID, DATA):
        self.send(ID, DATA)

    ##############################
    ########### Sensors ##########
    ##############################

    def sensor_resetAll(self, id):
        settingID = 0
        DATA = [VERIFICATIONID, id, settingID]
        self.send(NODEID, DATA)

    def sensor_setSampleRate(self, id, mode):
        if isinstance(mode, str):
            mode = mode.upper()

            modes = dict(SLOW=1, MEDIUM=2, FAST=3)
            if mode in modes:
                DATA = [VERIFICATIONID, id, modes[mode]]
                self.send(NODEID, DATA)
        return mode

    def sensor_setAlphaEMA(self, id, var, label):
        settingID = 4
        if intTypeCheck(var, int, label, 8):
            binstr = bitstring.BitArray(int=int(var.get()), length=8).bin
            DATA = [VERIFICATIONID, id, settingID, int(binstr[0:8], 2)]
            self.send(NODEID, DATA)

    ##############################
    ########### Valves ###########
    ##############################
    
    def valve_valveActuation(self, commandID, state, offState, onState):
        DATA = [offState if state else onState]
        self.send(commandID, DATA)

    def valve_resetAll(self, id):
        settingID = 0
        DATA = [VERIFICATIONID, id, settingID]
        self.send(NODEID, DATA)

    def valve_setValveType(self, id, val):
        settingID = 1
        if isinstance(val, str):
            val = val.upper()
            print(val)
            if val == "NORMALLY CLOSED":
                DATA = [VERIFICATIONID, id, settingID, 0]
                self.send(NODEID, DATA)
            elif val == "NORMALLY OPEN":
                DATA = [VERIFICATIONID, id, settingID, 1]
                self.send(NODEID, DATA)

    def valve_updateSetting(self, id, var, label, settingID, length=32):
        if intTypeCheck(var, int, label, length):
            binstr = bitstring.BitArray(int=int(var.get()), length=length).bin
            DATA = [VERIFICATIONID, id, settingID] + [int(binstr[i:i+8], 2) for i in range(0, length, 8)]
            self.send(NODEID, DATA)

    def valve_setFullDutyTime(self, id, var, label):
        self.valve_updateSetting(id, var, label, 2, length=32)

    def valve_setFullDutyCyclePWM(self, id, var, label):
        self.valve_updateSetting(id, var, label, 3, length=16)

    def valve_setHoldDutyCyclePWM(self, id, var, label):
        self.valve_updateSetting(id, var, label, 4, length=8)

    def valve_setWarmDutyCyclePWM(self, id, var, label):
        self.valve_updateSetting(id, var, label, 5, length=16)

    def valve_setLiveOutTime(self, id, var, label):
        self.valve_updateSetting(id, var, label, 1, length=32)

    ##############################
    ########### States ###########
    ##############################

    def state_StateActuation(self, commandID, state, offState, onState):
        DATA = [onState if state else offState]
        self.send(commandID, DATA)

    ##############################
    ######### Controller #########
    ##############################

    def controller_updateSetting(self, id, var, label, settingID, length=32, Type=float):
        if intTypeCheck(var, Type, label, length):
            if Type == float:
                binstr = bitstring.BitArray(float=float(var.get()), length=length).bin
            if Type == int:
                binstr = bitstring.BitArray(int=int(var.get()), length=length).bin
            DATA = [VERIFICATIONID, id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            self.send(NODEID, DATA)

    def controller_updateActuation(self, id, var, label, settingID, length=32):
        if intTypeCheck(var, int, label, length):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=length).bin
            DATA = [VERIFICATIONID, id, settingID, int(binstr[0:8],2), int(binstr[8:16],2), int(binstr[16:24],2), int(binstr[24:32],2)]
            self.send(NODEID, DATA)

    def controller_resetAll(self, id):
        DATA = [VERIFICATIONID, id, 0]
        self.send(NODEID, DATA)

    def controller_setFuelMVAutosequenceActuation(self, id, var, label):
        self.controller_updateActuation(id, var, label, 1)

    def controller_setLoxMVAutosequenceActuation(self, id, var, label):
        self.controller_updateActuation(var, id, label, 2)

    def controller_setIgniter1ActuationActuation(self, id, var, label):
        self.controller_updateActuation(var, id, label, 3)

    def controller_setIgniter2ActuationActuation(self, id, var, label):
        self.controller_updateActuation(var, id, label, 4)

    def controller_setThrottleProgramPoint(self, id, time, throttlepoint, label):
        settingID = 5
        if intTypeCheck(time, int, label, 16):
            timebin = bitstring.BitArray(int=int(time.get()), length=16).bin
            throttle = bitstring.BitArray(int=int(throttlepoint.get()), length=16).bin
            DATA = [VERIFICATIONID, id, settingID, int(timebin[0:8], 2), int(timebin[8:16], 2),
                    int(throttle[0:8], 2), int(throttle[8:16], 2)]
            self.send(NODEID, DATA)

    def controller_throttleProgramReset(self, id):
        settingID = 6
        DATA = [VERIFICATIONID, id, settingID]
        self.send(NODEID, DATA)

    # This one is too different to generalize.
    # On second thought, maybe this is the same as the throttle set?
    def controller_throttleProgramResetSpecific(self, id, time, throttlepoint, label):
        settingID = 7
        if intTypeCheck(time, int, label, 16):
            binstr = bitstring.BitArray(int=int(time.get()), length=16).bin
            binstr.append(bitstring.BitArray(int=int(throttlepoint.get()), length=16).bin)
            DATA = [VERIFICATIONID, id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            self.send(NODEID, DATA)

    def controller_setK_p(self, id, var, label):
        self.controller_updateSetting(var, id, label, 1)

    def controller_setK_i(self, id, var, label):
        self.controller_updateSetting(var, id, label, 2)

    def controller_setK_d(self, id, var, label):
        self.controller_updateSetting(var, id, label, 3)

    def controller_setControllerThreshold(self, id, var, label):
        self.controller_updateSetting(var, id, label, 4)

    def controller_setVentFailsafePressure(self, id, var, label):
        self.controller_updateSetting(var, id, label, 5)

    def controller_setValveMinimumEnergizeTime(self, id, var, label):
        self.controller_updateSetting(var, id, label, 6, Type=int)

    def controller_setValveMinimumDeenergizeTime(self, id, var, label):
        self.controller_updateSetting(var, id, label, 7, Type=int)

    def controller_setCountdownStart(self, id, var, label):
        settingID = 1
        if intTypeCheck(var, int, label, 32):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=32).bin
            DATA = [VERIFICATIONID, id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            self.send(NODEID, DATA)

class CanReceive:
    VehicleStates = [
        "Setup",
        "Passive",
        "Standby",
        "Test",
        "Abort",
        "Vent",
        "OFF Nominal",
        "Hi Press Arm",
        "Hi Press Pressurized",
        "Tank Press Arm",
        "Tank Press Pressurized",
        "Fire Arm",
        "Fire"
        ]
    
    def __init__(self, channel='can0', bustype='socketcan'):
        print("RocketDriver2 CanReceive instance created")
        self.loop = True
        self.busargs = {'channel':channel, 'bustype':bustype}

        self.Sensors = [0] * 1028
        self.sensorTimestamps = [0] * 1028
        self.Valves = [0] * 64
        self.ValvesRenegadeEngine = [0] * 64
        self.ValvesRenegadeProp = [0] * 64
        self.Controllers = [[0] * 50 for i in range(12)]

        self.NodeStatusBang = CanReceive.VehicleStates[0]
        self.NodeStatusRenegadeEngine = CanReceive.VehicleStates[0]
        self.NodeStatusRenegadeProp = CanReceive.VehicleStates[0]

        self.AutosequenceTime = 0
        self.ThrottlePoints = {}
        self.AutosequenceTimeDupes = 0

    def run(self):
        # starts Canbus
        #bus_type = 'virtual'#'socketcan'
        #channel0 = 'vcan0'
        bus_receive = can.interface.Bus(**self.busargs)#channel=channel0, bustype=bus_type)
        ###print("initializing new can")
        ###print()
        ###yield # initial yield to init the bus. Why isn't this in init??
        
        while self.loop:
            ###print("waiting for message in...")
            msg_in = bus_receive.recv(timeout=None)
            ###print("bus mentioned")

            try:
                ID_A, msg_id_bin, data_bin, data_list_hex = \
                      self.parseMessage(msg_in)
            except Exception as e:
                print(e)
                continue
        
            ###print("parsed message as:")
            ###print(ID_A, data_list_hex)
            ###print("")
            ###print("translating message:")
            self.translateMessage(ID_A, msg_id_bin, data_bin, data_list_hex)
            ###print("")
            ###print("yield")
            ###yield

    def parseMessage(self, msg_in):
        # Grabs Message ID
        msg_id = int(msg_in.arbitration_id)
        msg_id_bin = str(bitstring.BitArray(int=msg_id, length=32).bin)
        ID_A_bin = msg_id_bin[-11:]
        ID_A = ba2int(bitarray(ID_A_bin))
        # Grabs the data in the msg
        data_list_hex = msg_in.data.hex()
        data_bin = bitstring.BitArray(hex=data_list_hex).bin

        # if data is empty
#       if data_list_hex[0:16] == '':
#           continue
        
        return ID_A, msg_id_bin, data_bin, data_list_hex
    
    def translateMessage(self, ID_A, msg_id_bin, data_bin, data_list_hex):

        if ID_A == 546:
            self.ID_546(ID_A, msg_id_bin, data_bin, data_list_hex)
        if ID_A == 552:
            self.ID_552(ID_A, msg_id_bin, data_bin, data_list_hex)
        if ID_A == 547:
            self.ID_547(ID_A, msg_id_bin, data_bin, data_list_hex)
        elif 510 < ID_A < 530:
            self.ID_Between_510_530(ID_A, msg_id_bin, data_bin, data_list_hex)
        elif 50 < ID_A < 427:
            self.ID_Between_050_427(ID_A, msg_id_bin, data_bin, data_list_hex)
            

        elif ID_A > 1000:
            self.translateControllerMessage(ID_A, msg_id_bin, data_bin, data_list_hex)

    def translateControllerMessage(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        " CONTROLLERS"
        #print(ID_A)

        if ID_A == 1100:
            self.ID_1100_Controller(ID_A, msg_id_bin, data_bin, data_list_hex)
        elif ID_A == 1506:
            self.ID_1506_Controller(ID_A, msg_id_bin, data_bin, data_list_hex)
        elif data_list_hex:
            self.ID_Misc_Controller(ID_A, msg_id_bin, data_bin, data_list_hex)

    def ID_546(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        """
        Valves
        
        """
        #print(msg_id_bin, data_bin)
        HP1_bin = int(msg_id_bin[12:20])
        HP1_bin = str(HP1_bin)[::-1]
        if HP1_bin:
            HP1 = ba2int(bitarray(HP1_bin))
            #print(HP1)
            #print(msg_id_bin)
            self.ValvesRenegadeEngine[1] = HP1

        HP2_bin = int(msg_id_bin[4:12])
        HP2_bin = str(HP2_bin)[::-1]
        HP2 = ba2int(bitarray(HP2_bin))

        self.ValvesRenegadeEngine[2] = HP2
        for i in range(3, 11):
            HPi_bin = data_bin[(i - 3) * 8:(i - 2) * 8]
            HPi = ba2int(bitarray(HPi_bin))
            self.ValvesRenegadeEngine[i] = HPi
    
    def ID_552(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        """
        Valves
        
        """
        #print(msg_id_bin, data_bin)
        HP1_bin = int(msg_id_bin[12:20])
        HP1_bin = str(HP1_bin)[::-1]
        if HP1_bin:
            HP1 = ba2int(bitarray(HP1_bin))
            #print(HP1)
            #print(msg_id_bin)
            self.Valves[1] = HP1

        HP2_bin = int(msg_id_bin[4:12])
        HP2_bin = str(HP2_bin)[::-1]
        HP2 = ba2int(bitarray(HP2_bin))

        self.Valves[2] = HP2
        for i in range(3, 11):
            HPi_bin = data_bin[(i - 3) * 8:(i - 2) * 8]
            HPi = ba2int(bitarray(HPi_bin))
            self.Valves[i] = HPi

    def ID_547(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        """
        Valves
        
        """
        #print(msg_id_bin, data_bin)
        HP1_bin = int(msg_id_bin[12:20])
        HP1_bin = str(HP1_bin)[::-1]
        if HP1_bin:
            HP1 = ba2int(bitarray(HP1_bin))
            #print(HP1)
            #print(msg_id_bin)
            self.ValvesRenegadeProp[1] = HP1

        HP2_bin = int(msg_id_bin[4:12])
        HP2_bin = str(HP2_bin)[::-1]
        HP2 = ba2int(bitarray(HP2_bin))

        self.ValvesRenegadeProp[2] = HP2
        for i in range(3, 11):
            HPi_bin = data_bin[(i - 3) * 8:(i - 2) * 8]
            HPi = ba2int(bitarray(HPi_bin))
            self.ValvesRenegadeProp[i] = HPi
    
    def ID_Between_510_530(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        "NODE STATES"
        "Engine Node 2"
        "Prop Node 3"
        try:
            if ID_A == 514: 
                self.NodeStatusRenegadeEngine = CanReceive.VehicleStates[int(data_list_hex[0:2], 16)]
            if ID_A == 515: 
                self.NodeStatusRenegadeProp = CanReceive.VehicleStates[int(data_list_hex[0:2], 16)]
            if ID_A == 520: 
                self.NodeStatusBang = CanReceive.VehicleStates[int(data_list_hex[0:2], 16)]
            self.translateMessage(ID_A, msg_id_bin, data_bin, data_list_hex)
        except:
            return
        
    def ID_Between_050_427(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        """
        Sensors
        """
        #print(ID_A, "NADA")
        if data_list_hex:
            TimeStamp_bin = msg_id_bin[0:18]
            TimeStamp = ba2int(bitarray(TimeStamp_bin))
            msg_id = ID_A
            value = ba2int(bitarray(data_bin[0:16]), signed = False)
            self.Sensors[msg_id] = value/10
            self.sensorTimestamps[msg_id] = TimeStamp
            #print(msg_id, value/10, data_list_hex,data_bin[0:16])
            if len(data_list_hex) > 6:
                msg_id_2 = int(data_list_hex[4:6], base=16)
                value_2 =  ba2int(bitarray(data_bin[24:40]), signed = False)
                self.Sensors[msg_id_2] = value_2/10
                self.sensorTimestamps[msg_id_2] = TimeStamp
                #print(msg_id_2, value_2/10, data_list_hex,data_bin[24:40])

            if len(data_list_hex) > 12:

                msg_id_3 = int(data_list_hex[10:12], base=16)
                value_3 = ba2int(bitarray(data_bin[48:64]), signed = False)
                self.Sensors[msg_id_3] = value_3/10
                self.sensorTimestamps[msg_id_3] = TimeStamp
                #print(msg_id_3, value_3/10, data_list_hex,data_bin[48:64])

    def ID_1100_Controller(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        "AUTOSEQUENCE"
        self.PrevAutosequenceTime = self.AutosequenceTime
        self.AutosequenceTime = ba2int(bitarray(data_bin), signed = True)/1000000

        if self.PrevAutosequenceTime == self.AutosequenceTime:
            self.AutosequenceTimeDupes += 1
        else:
            print(self.AutosequenceTimeDupes, "Dupes parsed.")
            print("Autosequence Time:", self.AutosequenceTime)
            self.AutosequenceTimeDupes = 0

    def ID_1506_Controller(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        Time = int(data_list_hex[0:4], base=16)
        ThrottlePoint = int(data_list_hex[4:8], base=16)
        if Time == 0:
            self.ThrottlePoints = []
        #print(Time, ThrottlePoint)
        self.ThrottlePoints.append([Time, ThrottlePoint])
        try:
            Time = int(data_list_hex[8:12], base=16)
            ThrottlePoint = int(data_list_hex[12:16], base=16)
            self.ThrottlePoints.append([Time, ThrottlePoint])
        except:
            return

    def ID_Misc_Controller(self, ID_A, msg_id_bin, data_bin, data_list_hex):
        ControllerID = (round(ID_A, -2)-1000)//100
        ControllerIndex = ID_A % 100
        if len(data_list_hex) == 16:
            
            if ID_A == 1502 or ID_A == 1504:
                value_1 = ba2int(bitarray(data_bin[0:32]), signed = True)
                self.Controllers[ControllerID][ControllerIndex] = value_1
                value_2 = ba2int(bitarray(data_bin[32:64]), signed = True)
                self.Controllers[ControllerID][ControllerIndex + 1] = value_2
            elif ControllerIndex == 14 or ControllerIndex == 15:
                value_1 = int(data_bin[0:32],2)
                self.Controllers[ControllerID][ControllerIndex] = value_1
                value_2 = int(data_bin[32:64],2)
                self.Controllers[ControllerID][ControllerIndex + 1] = value_2
            else:
                value_1 = int(data_bin[0:32],2)
                value_1 = struct.unpack('f', struct.pack('I', value_1))[0]
                self.Controllers[ControllerID][ControllerIndex] = value_1
                value_2 = int(data_bin[32:64],2)
                value_2 = struct.unpack('f', struct.pack('I', value_2))[0]
                self.Controllers[ControllerID][ControllerIndex + 1] = value_2
        else:
            
            value_1 = int(data_bin[0:32],2)
            value_1 = struct.unpack('f', struct.pack('I', value_1))[0]
            self.Controllers[ControllerID][ControllerIndex] = value_1



