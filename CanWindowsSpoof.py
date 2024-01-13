
# Joseph Kessler
# 2024 January 12
# CanWindowsSpoof.py
################################################################################
#    This script spoofs the can module for testing the GUI for BLT's Avionics
# subsystem.  The script was originally desgned to be ran on a Raspberry pi, and
# as such does not have onboard windows compatibility.

################################################################################
# This is the original, unspoofed code.
#import can

################################################################################
# Can spoofing code
#
#     The following line is the only apparent reference to the can libaray
# throughout the GUI:
# 
# bus_receive = can.interface.Bus(channel=channel0, bustype=bus_type)
#
# The following code spoofs can.interface to contain a spoofed Bus class:

# This is copy-pasted from the following link:
# https://docs.python.org/3/library/types.html#types.SimpleNamespace
import types
import time
class SimpleNamespace:
    def __init__(self, /, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        items = (f"{k}={v!r}" for k, v in self.__dict__.items())
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        if isinstance(self, SimpleNamespace) and isinstance(other, SimpleNamespace):
           return self.__dict__ == other.__dict__
        return NotImplemented

class MessageSpoofer:
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.data = msg.encode()
        self.arbitration_id = 0
        self.__dict__.update(kwargs)

    def __eq__(self):
        return self.msg

class CanbusSpoofer:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        print("Created spoofed canbus with parameters:")
        for k,v in self.__dict__.items():
            print(k, v)
    
    def send(msg):
        print("bus.send called with msg:", msg)    

    def recv(*args, **kwargs):
        packet = "0,0,1,3,0,0,103,58239,0,0"
        
        print("bus.recv called. with args:", *args, kwargs)
        print("Waiting 1 second, then sending this packet:", packet)
        time.sleep(1)
        return MessageSpoofer(packet)



    

can = SimpleNamespace()
can.Message = lambda **kwargs: str(kwargs)

can.interface = SimpleNamespace()
can.interface.Bus = CanbusSpoofer

if __name__ == '__main__':
    print("Can spoofer script.  Produces the following fake module:")
    print(can)
    print()
    bus_type = 'socketcan'
    channel0 = 'can0'
    bus_receive = can.interface.Bus(channel=channel0, bustype=bus_type)
