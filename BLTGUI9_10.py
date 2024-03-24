# Import the library tkinter
from tkinter import *
from tkinter import font as tkFont  # for font size
from threading import Thread
from PIL import Image, ImageTk
from os.path import exists
import bitstring
import datetime
import random
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)
from matplotlib import style

# # This code is initializing the bus variable with the channel and bustype.
# # noinspection PyTypeChecker

CanStatus = False
try:
    import can  # /////////////////////////////////////////////////////////////////////////

    #bus = can.interface.Bus(channel='can0', bustype='socketcan')  # ///////////////
    bus = can.interface.Bus(channel='virtual', bustype='virtual')  # ///////////////
    CanStatus = True
    from CanReceive import CanReceive
    canReceive = None

except AttributeError:
    CanStatus = False
except ModuleNotFoundError:
    pass


def CanBusSend(ID, DATA):
    print(DATA)
    if CanStatus:
        msg = can.Message(arbitration_id=ID,
                          data=DATA, is_extended_id=False)
        bus.send(msg)


style.use("dark_background")

REFRESHRATE = 250  # ms
GRAPHDATAREFRESHRATE = 250  # ms

# This code is initializing the bus variable with the channel and bustype.
# noinspection PyTypeChecker
# bus = can.interface.Bus(channel='can0', bustype='socketcan')  # ///////////////

yellow = "yellow3"
blue = "dodgerblue"
red = "red"
green = "green"
purple = "purple4"
darkGrey = "grey3"
orange = 'orange'
black = "black"
grey = "grey35"
white = "white"
DANGERZONE = 300

NODEID = 8
VERIFICATIONID = 166

class Graph:
    def __init__(self, label, parent, relx, rely, bg=black):
        self.label = label
        self.frame = Canvas(parent, bg=bg)
        self.frame.place(relx=relx, rely=rely, relwidth=.225, relheight=2 / 5)
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvasfigure = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.axis = self.figure.add_subplot()
        self.canvasfigure.get_tk_widget().pack()

class Main:
    # Data needed to set up the Valve, Sensors, States
    # [ Valve Name, relx ,rely , Object ID , commandID, commandOFF , commandON, ]

    # Name, Relx, Rely , Object ID, HP Channel, Command OFF, Command ON, sensorID, nodeID
    valves = [
        ['HV',   .55,  .25,   16, 2, 34, 35, yellow, 122, 2], 
        ['HP',   .6,   .15,   17, 1, 32, 33, yellow, 121, 2], 
        ['LDR',  .35,  .35,   19, 3, 38, 39, blue,   133, 3], 
        ['FDR',  .445, .35,   22, 7, 44, 45, red,    137, 3], 
        ['LDV',  .225, .35,   20, 4, 40, 41, blue,   134, 3], 
        ['FDV',  .55,  .35,   23, 8, 46, 47, red,    138, 3], 
        ['LV',   .275, .45,   18, 1, 36, 37, blue,   131, 3], 
        ['FV',   .535, .45,   21, 5, 42, 43, red,    135, 3], 
        ['LMV',  .35,  .6875, 24, 4, 48, 49, blue,   124, 2], 
        ['FMV',  .475, .6875, 25, 3, 50, 51, red,    123, 2], 
        ['IGN1', .475, .775,  26, 5, 52, 53, green,  125, 2], 
        ['IGN2', .475, .85,   27, 7, 54, 55, green,  127, 2]  
    ]
    # [ 
    # [ Sensor Name, relx ,rely , Reading Xcor Offest , Reading Ycor Offest,  Raw Sensor ID, Converted Sensor ID,
    # labelColor]
    sensors = [
        ["High\nPress 1",    0.475, 0.05,  0.0,   0.05, 70, 81, yellow],#, 1, 1],
        ["High\nPress 2",    0.525, 0.05,  0.0,   0.05, 72, 81, yellow],#, 1, 1],
        ["Fuel\nTank 1",     0.675, 0.600, 0.0,   0.05, 62, 81, red   ],#, 0.0258, -161.04],
        ["Lox Dome\nReg",    0.175, 0.700, 0.0,   0.05, 76, 81, blue  ],#, 0.0258, -161.04],
        ["Fuel Dome\nReg",   0.675, 0.700, 0.0,   0.05, 74, 81, red   ],#, 0.0258, -161.04],
        ["Lox\nTank 1",      0.225, 0.600, 0.0,   0.05, 66, 81, blue  ],#, 1, 1],
        ["Fuel\nTank 2",     0.725, 0.600, 0.0,   0.05, 64, 81, red   ],#, 0.0293, -190.04],
        ["Lox\nTank 2",      0.175, 0.600, 0.0,   0.05, 68, 81, blue  ],#, 1,1],
        ["Fuel\nProp Inlet", 0.725, 0.7,   0.0,   0.05, 58, 81, red   ],#, 1, 1],
        ["Lox\nProp Inlet",  0.225, 0.7,   0.0,   0.05, 60, 81, blue  ],#, 1, 1],
        ["Fuel\nInjector",   0.7,   0.8,   0.0,   0.05, 54, 81, red   ],#, 1, 1],
        ["LC1: ",            0.55,  0.7,   0.035, 0.0,  37, 37, green ],#, 1, 1],
        ["Chamber 1",        0.55,  0.6,   0.065, 0.0,  50, 51, green ],
        ["LC2: ",            0.55,  0.75,  0.035, 0.0,  43, 43, green ],#, 1, 1],
        ["Chamber 2",        0.55,  0.65,  0.065, 0.0,  52, 81, green ],
        ["LC3: ",            0.55,  0.8,   0.035, 0.0,  49, 49, green ],#, 1, 1],
        ["MV\nPneumatic",    0.4,   0.6,   0.01,  0.05, 56, 81, purple],#, 1, 1],

        #["Chamber 2", .55, 0.65, 0.065, 0, 20, 81, green],

    ]
    # [ State Name, State ID , commandID, commandOFF , commandON, IfItsAnArmState, StateNumber]
    States = [
        #["Active",              2, 1,  3,  5, False, 1],
        ["Test",                 2, 1,  3,  5, False, 1],
        ["Hi-Press\nPress Arm",  3, 1, 10, 11, True,  2],
        ["Hi-Press\nPressurize", 4, 1, 12, 13, False, 3],
        ["Tank Press \nArm",     5, 1, 14, 15, True,  4],
        ["Tank \nPressurize",    6, 1, 16, 17, False, 5],
        ["Fire Arm",             7, 1, 18, 19, True,  6],
        ["FIRE",                 8, 1, 20, 21, False, 7]
    ]
    Vent = [
        "Vent", 0.15, 1, 3, 9, False, 0
    ]
    Abort = [
        "Abort", .275, 1, 3, 7, False, 0
    ]
    Controllers = [
        #["Tank Controller HiPress", 2, False, black],
        #["Tank Controller Lox",     3, True,  blue ],
        #["Tank Controller Fuel",    4, True,  red  ],
        ["Engine Controller 1",      5, False, black],
        ["Auto Sequence",            1, False, black],
        ["Node Controller",          0, False, black],
    ]

    # System starts off in a passive state
    CurrState = "Passive"

    def __init__(self, canReceive):
        self.canReceive = canReceive

        self.appMainScreen = None
        self.parentMainScreen = None

        """ Manual Override """
        self.ManualOverridePhoto = None
        self.ManualOverrideButton = None
        self.overrideCommandID = 1
        self.overrideCommandOFF = 22
        self.overrideCommandON = 23

        self.sensorList = []
        self.valveList = []
        self.controllerList = []
        
        self.ThrottlePointsStorage = []
        
#         self.LOxSetPressure = 150
#         self.FuelSetPressure = 150

        self.manualOverrideState = False

        self.nodeCommandReset = 240
        self.nodeCommandID = 200

        self.ValveOptionsDropDownMenu = None
        self.statusLabel = None

        self.graphingStatus = True
        self.refreshCounter = True

    def imagePlacement(self):
        """ Propulsion System Diagram"""

        buffer = [
            ["GUI Images/Engine_Clipart.png",        dict(relx=.4,    rely=.775)],
            ["GUI Images/LOxTankClipart.png",        dict(relx=.3,    rely=.55 )],
            ["GUI Images/FuelTankClipart.png",       dict(relx=.5075, rely=.55 )],
            ["GUI Images/PressurantTankClipart.png", dict(relx=.405,  rely=.01 )]
        ]

        for src, iargs in buffer:
            img = Image.open(src)
            render = ImageTk.PhotoImage(img)
            label = Label(self.parentMainScreen, image=render, bg=black)
            label.image = render
            label.place(**iargs)
        
    def propLinePlacement(self):
        # Lines showing the fluid flow routing in the fluid system
        aFont = tkFont.Font(family="Verdana", size=15, weight="bold")

        # Vertex Buffer
        vb = [ 
            ( 800,   50), ( 800,  250), ( 600,  250), (1000,  250), ( 600,  400), ( 800,  400), ( 800,  175), (1200,  175), 
            (1000,  400), (1100,  175), (1100,  300), ( 800,  300), ( 500,  400), (1100,  400), ( 700,  600), ( 900,  600), 
            ( 800,  600), ( 900,  750), ( 700,  750), ( 600,  750), ( 785,  750), ( 785,  900), ( 600,  500), ( 500,  500), 
            (1000,  750), ( 815,  750), ( 815,  900), (1000,  500), (1100,  500), 
        ]

        # Index Buffer
        ib = [
            ( 0,  1), ( 2,  3), ( 2,  4), ( 1,  5), ( 6,  7), ( 3,  8), ( 9, 10), # High Pressure lines
            (11,  5), (12, 13), (14, 15), ( 5, 16), (15, 17), (14, 18),           # Pnumatics
            ( 4, 19), (19, 20), (20, 21), (22, 23),         # Lox
            ( 8, 24), (24, 25), (25, 26), (27, 28)          # Fuel
        ]

        colors = [yellow]*7 + [purple]*6 + [blue]*4 + [red]*4

        for (i0, i1), fill in zip(ib, colors):
            self.parentMainScreen.create_line(vb[i0], vb[i1], fill=fill, width=5)
        
        # These are the number value boxes.  Why are they here?
        self.parentMainScreen.create_rectangle(1275, 600, 1475, 850, outline=red,     fill=black)
        self.parentMainScreen.create_rectangle(300,  600, 500,  850, outline=blue,    fill=black)
        self.parentMainScreen.create_rectangle(1050, 600, 1250, 900, outline=green,   fill=black)
        self.parentMainScreen.create_rectangle(850,  30,  1100, 150, outline=yellow,  fill=black)
        self.parentMainScreen.create_rectangle(750,  625, 870,  725, outline=purple,  fill=black)
        
        # This holds the control buttons on the left.
        self.parentMainScreen.create_rectangle(10, 160, 275, 1020, outline=orange, fill=black, width=5)

        # Second display value boxes.
        self.parentSecondScreen.create_rectangle(450, 10, 750, 550, outline=orange, fill=black, width=5)
        self.parentSecondScreen.create_rectangle(10, 10, 425, 800, outline=orange, fill=black, width=5)
        
        # Second display ENGINE CONTROLLER BOX
        self.parentSecondScreen.create_rectangle(775, 475, 1125, 900, outline=green, fill=black, width=5)

        self.SensorsLabel = Label(self.parentSecondScreen, fg=orange, bg=black, font=aFont, text="SENSORS")
        self.SensorsLabel.place(relx=.09, rely=0.025)
        self.ValvesLabel = Label(self.parentSecondScreen, fg=orange, bg=black, font=aFont, text="VALVES")
        self.ValvesLabel.place(relx=.285, rely=0.025)
        self.FuelControllerLabel = Label(self.parentSecondScreen, fg=green, bg=black, font=aFont, text="ENGINE CONTROLLER")
        self.FuelControllerLabel.place(relx=.435, rely=0.475)

    def ManualOverride(self, event):
        if Main.CurrState != "Override":
            self.savedCurrState = Main.CurrState
            for i in range(len(Main.States)):
                if Main.States[i][0] == Main.CurrState:
                    self.reminderButtonOfCurrState = Button(self.parentMainScreen, text=Main.CurrState,
                                                            fg='orange', bg='black', bd=5, font=20)
                    # Goes to logic function when button is pressed
                    self.reminderButtonOfCurrState.place(relx=0.0125, rely=1 - (1 / len(Main.States) / 2) * (
                            len(Main.States) - Main.States[i][6] + 1) - .05, relheight=1 / len(Main.States) / 2,
                                                         relwidth=0.125)
        if self.manualOverrideState:
            self.photo = PhotoImage(file="GUI Images/ManualOverrideDisabledButton.png")
            self.Button = Button(self.parentMainScreen, image=self.photo, fg='red', bg='black', bd=5)
            self.parentMainScreen.killSwitchState = False
            self.reminderButtonOfCurrState.destroy()
            Main.CurrState = self.savedCurrState
            # msg = can.Message(arbitration_id=self.overrideCommandID, data=[self.overrideCommandON], is_extended_id=False)
            # bus.send(msg)
        else:
            self.photo = PhotoImage(file="GUI Images/ManualOverrideEnabledButton.png")
            self.Button = Button(self.parentMainScreen, image=self.photo, fg='green', bg='black', bd=5)
            self.manualOverrideState = True
            Main.CurrState = "Override"
            # msg = can.Message(arbitration_id=self.overrideCommandID, data=[self.overrideCommandOFF], is_extended_id=False)
            # bus.send(msg)
        self.Button.place(relx=.7, rely=0.2)
        self.Button.bind('<Double-1>', self.ManualOverride)  # bind double left clicks

        # On double press, Call KillSwitch function
    def ThrottlePoints(self):
        if self.canReceive.ThrottlePoints != self.ThrottlePointsStorage:
            self.ThrottlePointsStorage = self.canReceive.ThrottlePoints
            aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
            print(self.canReceive.ThrottlePoints)
            for throttlepoint in range(len(self.canReceive.ThrottlePoints)):
                Timelabel = Label(self.parentSecondScreen, text = "T + " + str(self.canReceive.ThrottlePoints[throttlepoint][0]), fg = green, bg = black, font = aFont)
                Timelabel.place(relx = 0.6, rely = 0.5 + throttlepoint*.1)
                Pressurelabel = Label(self.parentSecondScreen, text = "Pressure: "+ str(self.canReceive.ThrottlePoints[throttlepoint][1]), fg = green, bg = black, font = aFont)
                Pressurelabel.place(relx = 0.65, rely = 0.5 + throttlepoint*.1)
    
    # Readings Refresher, Recursive Function
    def Refresh(self):
        if self.refreshCounter >= REFRESHRATE:
            self.refreshCounter = 0
            # for each sensor in the sensor list. refresh the label
            legendsGraphs = []
            for i in range(len(self.graphs)):
                legendsGraphs.append([])
                self.graphs[i].axis.clear()
            
            #self.ThrottlePoints()
            
            for sensor in self.sensorList:
                sensor.Refresh(True)
                if self.graphingStatus:
                    for status, legend, graph in zip(sensor.GraphStatus, legendsGraphs, self.graphs):
                        if status.get():
                            graph.axis.plot(sensor.sensorData, label=sensor.name)
                            graph.figure.canvas.draw()
                            legend.append(sensor.name)

            for legend, graph in zip(legendsGraphs, self.graphs):
                if legend:
                    graph.axis.legend(legend, loc="upper left")
                    graph.figure.canvas.draw()

            for valve in self.valveList:
                valve.refresh_valve()
            for controller in self.controllerList:
                controller.Refresh()

            self.autosequence_str = "T  " + str(self.canReceive.AutosequenceTime) + " s"
            self.autoseqence.config(text=self.autosequence_str)
            self.time.config(text=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            #self.nodeState.config(text=self.canReceive.NodeStatus)  # can_receive.node_dict_list[self.name]["state"]))

            self.sensorList[1].ReadingLabel.after(GRAPHDATAREFRESHRATE, self.Refresh)
        else:
            for sensor in self.sensorList:
                sensor.Refresh(False)
                self.refreshCounter += GRAPHDATAREFRESHRATE

            self.sensorList[1].ReadingLabel.after(GRAPHDATAREFRESHRATE, self.Refresh)
            
        self.EngineNodeState.config(text = "Engine Node State: " + self.canReceive.NodeStatusRenegadeEngine)
        self.PropNodeState.config(text = "Prop Node State: " + self.canReceive.NodeStatusRenegadeProp)

    def StateReset(self):
        Main.CurrState = "Passive"
        # Store previosly instantiated State. Arm States may be able to access the state before it
        prevState = None
        # Every state in State Array gets instantiated and a Button is made for it
        for i in range(len(Main.States)):
            button = States(self.parentMainScreen, Main.States[i], prevState=prevState)
            # Creates the button and places it into the Frame. May change name later since it really inst instantiating
            button.MainStateInstantiation()
            # Updates the prevState so that the next state may be able to access it. Its pretty much a Linked List
            prevState = button

    def AutoSequence(self):
        self.autoseqence = Label(self.parentMainScreen, text="Boom Boom \n wont go boom boom", bg="black", fg="Green",
                                 font=("Verdana", 25))
        self.autoseqence.place(relx=.3, rely=0.1)
        self.autosequence_str = ""

    def PauseGraphs(self):
        #print(self.graphingStatus)
        self.graphingStatus = not self.graphingStatus

    def GenerateGraphs(self):
        self.pauseButton = Button(self.parentSecondScreen, font=("Verdana", 10), fg='red', bg='black',
                                  text="GRAPH PAUSE\nBUTTON", command=lambda: self.PauseGraphs())
        self.pauseButton.place(relx=.85, rely=.45)

        self.graphs = [
            Graph("Graph 1", self.parentMainScreen,   .775, .1 ),
            Graph("Graph 2", self.parentMainScreen,   .775, .6 ),
            Graph("Graph 3", self.parentSecondScreen, .775, .05),
            Graph("Graph 4", self.parentSecondScreen, .775, .5 ),
        ]

    def ValveSettingsPopUp(self):
        """
        Creates Pop Up Window with a Drop down menu with all the valve
        when a valve is chosen FunctionsDropDownMenu appears with the options available for that valve
        After a Operation is chosen Valve Set Function is called to do the Entry check and sends the command
        """
        self.ValveSetsPopUp = Toplevel(self.appMainScreen, background=grey)
        self.ValveSetsPopUp.geometry("750x250")
        self.chosenValveFunction = None
        clicked = StringVar()
        clicked.set("Choose Valve")
        self.valveOptions = []
        for valve in self.valveList:
            self.valveOptions.append(valve.name)
        self.ValveChoiceDropDown = OptionMenu(self.ValveSetsPopUp, clicked, *self.valveOptions,
                                              command=lambda Valve2: self.FunctionsDropDownMenu(Valve2, "Valve"))
        self.ValveChoiceDropDown.place(relx=0.2, rely=0.5)
        self.ValveFunctionLabel = Label(self.ValveSetsPopUp, bg=grey)
        self.ValveFunctionLabel.place(relx=.5, rely=0.4)

    def SensorSettingsPopUp(self):
        self.SensorSetsPopUp = Toplevel(self.appMainScreen, background=grey)
        self.SensorSetsPopUp.geometry("750x250")
        self.chosenSensorFunction = None
        clicked = StringVar()
        clicked.set("Choose Sensor")
        self.sensorOptions = []
        for sensor in self.sensorList:
            self.sensorOptions.append(sensor.name)
        self.SensorChoiceDropDown = OptionMenu(self.SensorSetsPopUp, clicked, *self.sensorOptions,
                                               command=lambda Sensor2: self.FunctionsDropDownMenu(Sensor2, "Sensor"))
        self.SensorChoiceDropDown.place(relx=0.2, rely=0.5)
        self.SensorFunctionLabel = Label(self.SensorSetsPopUp, bg=grey)
        self.SensorFunctionLabel.place(relx=.5, rely=0.4)

    def ControllerSettingsPopUp(self):
        self.ControllerPopUp = Toplevel(self.appMainScreen, background=grey)
        self.ControllerPopUp.geometry("750x250")
        self.chosenTankPressFunction = None
        clicked = StringVar()
        clicked.set("Choose Tank Press Controller")
        self.ControllerOptions = []
        for controller in self.controllerList:
            self.ControllerOptions.append(controller.name)
        self.ControllerChoiceDropDown = OptionMenu(self.ControllerPopUp, clicked, *self.ControllerOptions,
                                                   command=lambda Sensor2: self.FunctionsDropDownMenu(Sensor2,
                                                                                                      "Tank Press Controller"))
        self.ControllerChoiceDropDown.place(relx=0.2, rely=0.5)
        self.ControllerFunctionLabel = Label(self.ControllerPopUp, bg=grey)
        self.ControllerFunctionLabel.place(relx=.5, rely=0.4)

    def FunctionsDropDownMenu(self, object, type):
        if type == "Valve":
            for valve in self.valveList:
                if valve.name == object:
                    self.chosenValve = valve
                    break
            clicked2 = StringVar()
            clicked2.set("Choose Function")
            self.valveSetFunctions = [
                "Reset", "Valve Type", "Full Duty Time", "Full Duty Cycle PWM",
                "Hold Duty Cycle PWM", "Warm Duty Cycle PWM",
            ]
            if "IGN" in object:
                self.valveSetFunctions = [
                    "Reset", "Live Out Time"
                ]
            self.ValveOptionsDropDownMenu = OptionMenu(self.ValveSetsPopUp, clicked2, *self.valveSetFunctions,
                                                       command=lambda
                                                           Function: self.ValveSetFunction(Function))
            self.ValveOptionsDropDownMenu.config(width=20)
            self.ValveOptionsDropDownMenu.place(relx=0.2, rely=0.7)
            if self.chosenValveFunction is not None:
                self.ValveFunctionLabel.config(text=self.chosenValve.name + " " + self.chosenValveFunction)
        elif type == "Sensor":
            for sensor in self.sensorList:
                if sensor.name == object:
                    self.chosenSensor = sensor
                    break
            clicked2 = StringVar()
            clicked2.set("Choose Function")
            self.sensorSetFunctions = [
                "Reset", "Sample Rate"
            ]
            self.SensorOptionsDropDownMenu = OptionMenu(self.SensorSetsPopUp, clicked2, *self.sensorSetFunctions,
                                                        command=lambda
                                                            Function: self.SensorSetFunction(Function))
            self.SensorOptionsDropDownMenu.config(width=20)
            self.SensorOptionsDropDownMenu.place(relx=0.2, rely=0.7)
            if self.chosenSensorFunction is not None:
                self.SensorFunctionLabel.config(text=self.chosenSensor.name + " " + self.chosenSensorFunction)
        elif type == "Tank Press Controller":
            for Controller in self.controllerList:
                if Controller.name == object:
                    self.chosenController = Controller
                    break
            clicked2 = StringVar()
            clicked2.set("Choose Function")

            self.ControllerSetFunctions = [
                "Reset",
            ]

            if "Engine" in object:
                self.ControllerSetFunctions = [
                    "Reset",
                    "Fuel MV Autosequence Actuation",
                    "Lox MV Autosequence Actuation",
                    "Igniter 1 Actuation",
                    "Igniter 2 Actuation",
                ]

            if "Auto Sequence" in object:
                self.ControllerSetFunctions = [
                    "Reset",
                    "Countdown Start",
                ]

            self.TankPressControllerOptionsDropDownMenu = OptionMenu(self.ControllerPopUp, clicked2,
                                                                     *self.ControllerSetFunctions,
                                                                     command=lambda
                                                                         Function: self.ControllerSetFunction(Function))
            self.TankPressControllerOptionsDropDownMenu.config(width=20)
            self.TankPressControllerOptionsDropDownMenu.place(relx=0.2, rely=0.7)
            if self.chosenTankPressFunction is not None:
                self.ControllerFunctionLabel.config(text=self.chosenController[0] + " " + self.chosenTankPressFunction)

    def ValveSetFunction(self, Function):
        self.chosenValveFunction = Function
        self.ValveDataEntryButton = Button(self.ValveSetsPopUp, height=1, width=10, background="grey50", text="Enter")
        self.ValveDataEntryButton.place(relx=.5, rely=.7)
        self.ValveStatusLabel = Label(self.ValveSetsPopUp, font=("Helvetica", 12), bg=grey)
        self.ValveStatusLabel.place(relx=.7, rely=0.6)
        self.ValveSetData = StringVar()
        self.ValveSetDataEntry = Entry(self.ValveSetsPopUp, background="grey50", textvariable=self.ValveSetData)
        self.ValveSetDataEntry.place(relx=.5, rely=.5)
        self.ValveFunctionLabel.config(text=self.chosenValve.name + " " + self.chosenValveFunction)

        fptr = {
            "Reset":                self.chosenValve.resetAll,
            "Valve Type":           self.chosenValve.setValveType,
            "Full Duty Time":       self.chosenValve.setFullDutyTime,
            "Full Duty Cycle PWM":  self.chosenValve.setFullDutyCyclePWM,
            "Hold Duty Cycle PWM":  self.chosenValve.setHoldDutyCyclePWM,
            "Warm Duty Cycle PWM":  self.chosenValve.setWarmDutyCyclePWM,
            "Live Out Time":        self.chosenValve.intTypeCheck,
        }
        if Function == "Reset":
            self.ValveSetDataEntry.destroy()
        
        if Function in fptr:
            self.ValveDataEntryButton.config(
                command=lambda: fptr[Function](self.ValveSetData, self.statusLabel)
            )

    def SensorSetFunction(self, Function):
        self.chosenSensorFunction = Function
        self.SensorDataEntryButton = Button(self.SensorSetsPopUp, height=1, width=10, background="grey50", text="Enter")
        self.SensorDataEntryButton.place(relx=.5, rely=.7)
        self.SensorStatusLabel = Label(self.SensorSetsPopUp, font=("Helvetica", 12), bg=grey)
        self.SensorStatusLabel.place(relx=.7, rely=0.6)
        self.SensorSetData = StringVar()
        self.SensorSetDataEntry = Entry(self.SensorSetsPopUp, background="grey50", textvariable=self.SensorSetData)
        self.SensorSetDataEntry.place(relx=.5, rely=.5)
        self.SensorFunctionLabel.config(text=self.chosenSensor.name + " " + self.chosenSensorFunction)

        fptr = {
            "Reset":       self.chosenSensor.resetAll,
            "Sample Rate": self.chosenSensor.setSampleRate,
            "Alpha EMA":   self.chosenSensor.setAlphaEMA,
        }
        if Function == "Reset":
            self.SensorSetDataEntry.destroy()
        
        if Function in fptr:
            self.SensorDataEntryButton.config(
                command=lambda: fptr[Function](self.SensorSetData, self.SensorStatusLabel)
            )

    def ControllerSetFunction(self, Function):
        if Function == "ThrottleProgramPoint":
            self.chosenControllerFunction = Function
            self.ControllerDataEntryButton = Button(self.ControllerPopUp, height=1, width=10, background="grey50",
                                                    text="Enter")
            self.ControllerDataEntryButton.place(relx=.5, rely=.7)
            self.ControllerstatusLabel = Label(self.ControllerPopUp, font=("Helvetica", 12), bg=grey)
            self.ControllerstatusLabel.place(relx=.7, rely=0.6)
            timelabel = Label(self.ControllerPopUp, font=("Helvetica", 12), bg=grey, text = "T+ ")
            timelabel.place(relx=.65, rely=0.6)
            Pressurelabel = Label(self.ControllerPopUp, font=("Helvetica", 12), bg=grey, text = "PSI: ")
            Pressurelabel.place(relx=.75, rely=0.6)
            self.TimeSetData = StringVar()
            self.TimeSetDataEntry = Entry(self.ControllerPopUp, background="grey50",
                                                textvariable=self.TimeSetData)
            self.TimeSetDataEntry.place(relx=.6, rely=.5)
            self.PressureSetData = StringVar()
            self.PressureSetDataEntry = Entry(self.ControllerPopUp, background="grey50",
                                                textvariable=self.PressureSetData)
            self.PressureSetDataEntry.place(relx=.8, rely=.5)
            self.ControllerFunctionLabel.config(text=self.chosenController.name + " " + self.chosenControllerFunction)
            self.ControllerDataEntryButton.config(
                    command=lambda: self.chosenController.setThrottleProgramPoint(self.TimeSetData,self.PressureSetData,
                                                                                  self.ControllerstatusLabel))
        else:
            self.chosenControllerFunction = Function
            self.ControllerDataEntryButton = Button(self.ControllerPopUp, height=1, width=10, background="grey50",
                                                    text="Enter")
            self.ControllerDataEntryButton.place(relx=.5, rely=.7)
            self.ControllerstatusLabel = Label(self.ControllerPopUp, font=("Helvetica", 12), bg=grey)
            self.ControllerstatusLabel.place(relx=.7, rely=0.6)
            self.ControllerSetData = StringVar()
            self.ControllerSetDataEntry = Entry(self.ControllerPopUp, background="grey50",
                                                textvariable=self.ControllerSetData)
            self.ControllerSetDataEntry.place(relx=.5, rely=.5)
            self.ControllerFunctionLabel.config(text=self.chosenController.name + " " + self.chosenControllerFunction)

            fptr = {
                "Reset":                                        self.chosenController.resetAll,
                "Kp":                                           self.chosenController.setK_p,
                "Ki":                                           self.chosenController.setK_i,
                "Kd":                                           self.chosenController.setK_d,
                "Controller Threshold":                         self.chosenController.setControllerThreshold,
                "Vent Fail Safe Pressure":                      self.chosenController.setVentFailsafePressure,
                "Valve Minimum Energize Time":                  self.chosenController.setValveMinimumEnergizeTime,
                "Valve Minimum Deenergize Time":                self.chosenController.setValveMinimumDeenergizeTime,
                "Fuel MV Autosequence Actuation":               self.chosenController.setFuelMVAutosequenceActuation,
                "Lox MV Autosequence Actuation":                self.chosenController.setLoxMVAutosequenceActuation,
                "Igniter 1 Actuation":                          self.chosenController.setIgniter1ActuationActuation,
                "Igniter 2 Actuation":                          self.chosenController.setIgniter2ActuationActuation,
                "ThrottleProgramPoint":                         self.chosenController.setThrottleProgramPoint,
                "Throttle Program Reset ALL":                   self.chosenController.throttleProgramReset,
                "Throttle Program Reset Specific Target Point": self.chosenController.throttleProgramResetSpecific,
                "Countdown Start":                              self.chosenController.setCountdownStart,
            }

            if Function == "Reset" or Function == "Throttle Program Reset ALL":
                self.ControllerSetDataEntry.destroy()
            
            if Function in fptr:
                self.ControllerDataEntryButton.config(
                    command=lambda: fptr[Function](self.ControllerSetData, self.ControllerstatusLabel)
                )

    def NodeReset(self):
        DATA = [254]
        CanBusSend(1, DATA)

    def Menus(self, parent, app):
        self.menu = Menu(parent, background="grey50", fg=black)
        self.fileMenu = Menu(self.menu)

        # Dropdown menus in the top left
        self.graphsMenu = Menu(self.menu)
        self.graphsSubmenus = [Menu(self.menu) for g in self.graphs]

        self.SetPoints = Menu(self.menu)
        self.TeensyNodes = Menu(self.menu)
        self.DataRequests = Menu(self.menu)
        self.SensorSets = Menu(self.menu)
        #self.AutoSequenceMenu = Menu(self.menu)

        for menu, graph in zip(self.graphsSubmenus, self.graphs):
            self.graphsMenu.add_cascade(label=graph.label, menu=menu)
        
        self.menu.add_cascade(label="Graphs", menu=self.graphsMenu)
        self.menu.add_cascade(label="Set Points", menu=self.SetPoints)
        self.menu.add_cascade(label="Teensy Nodes", menu=self.TeensyNodes)
        self.menu.add_cascade(label="Data Requests", menu=self.DataRequests)

        #self.AutoSequenceMenu.add_command(label="Reset", command=lambda: self.AutoSequenceReset())
        #self.AutoSequenceMenu.add_command(label="Count Down Start", command=lambda: self.AutoSequenceSettings())

        self.SetPoints.add_command(label="Valves", command=lambda: self.ValveSettingsPopUp())
        self.SetPoints.add_command(label="Sensors", command=lambda: self.SensorSettingsPopUp())
        #self.SetPoints.add_cascade(label="Auto Sequence", menu=self.AutoSequenceMenu)
        self.SetPoints.add_command(label="Controllers", command=lambda: self.ControllerSettingsPopUp())

        self.TeensyNodes.add_command(label="Teensy Node Reset", command=lambda: self.NodeReset())

        app.config(menu=self.menu)

        for sensor in self.sensorList:
            for menu, status in zip(self.graphsSubmenus, sensor.GraphStatus):
                menu.add_checkbutton(label=sensor.name, variable=status)

    def run(self):  # This takes place of the init
        """ TKinter Initialization"""
        self.root = Tk()
        self.appMainScreen = Toplevel(self.root)
        self.appMainScreen.configure(background=black)
        self.appMainScreen.geometry("1920x1080")

        self.appSecondScreen = Toplevel(self.root)
        self.appSecondScreen.configure(background=black)
        self.appSecondScreen.geometry("1920x1080+1920+0")

        """ Main Canvas Initialization"""
        self.parentMainScreen = Canvas(self.appMainScreen, bg=black, highlightbackground=black, highlightthickness=0)
        self.parentMainScreen.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.parentSecondScreen = Canvas(self.appSecondScreen, bg=black, highlightbackground=black,
                                         highlightthickness=0)
        self.parentSecondScreen.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        
        self.PropNodeState = Label(self.parentMainScreen, text="Prop Node State", fg=orange, bg=black, font=("Arial", 25))
        self.PropNodeState.place(relx=.01, rely=0.02)
        self.EngineNodeState = Label(self.parentMainScreen, text="Engine Node State", fg=orange, bg=black, font=("Arial", 25))
        self.EngineNodeState.place(relx=.01, rely=0.07)
        
        self.imagePlacement()
        self.propLinePlacement()
        self.AutoSequence()
        self.StateReset()
        self.GenerateGraphs()
        self.Vent = States(self.parentMainScreen, Main.Vent)
        self.Vent.VentAbortInstantiation()
        self.Abort = States(self.parentMainScreen, Main.Abort)
        self.Abort.VentAbortInstantiation()
        # Instantiates Every Valve
        for valve in Main.valves:
            self.valveList.append(Valves(self.parentMainScreen, valve, self.parentSecondScreen, self.canReceive))

        # Instantiates Every Sensor
        for sensor in Main.sensors:
            self.sensorList.append(Sensors(self.parentMainScreen, sensor, self.parentSecondScreen, self.canReceive, self.graphs))

        # Instantiates Every Sensor
        for controller in Main.Controllers:
            self.controllerList.append(Controller(controller, self.parentMainScreen, self.parentSecondScreen, self.canReceive))

        self.Menus(self.parentMainScreen, self.appMainScreen)
        self.Menus(self.parentSecondScreen, self.appSecondScreen)

        self.time = Label(self.parentMainScreen, fg="Orange", bg=black,
                          text=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), font=("Verdana", 17))
        self.time.place(relx=.85, rely=0.01)

#         self.ManualOverridePhoto = PhotoImage(file="GUI Images/ManualOverrideDisabledButton.png")
#         self.ManualOverrideButton = Button(self.parentMainScreen, image=self.ManualOverridePhoto, fg='red', bg='black',
#                                            bd=5)
#         self.ManualOverrideButton.place(relx=.7, rely=0.2)
#         self.ManualOverrideButton.bind('<Double-1>', self.ManualOverride)  # bind double left clicks

        

        # RefreshLabel() Refreshes the Readings
        self.Refresh()

        """ Runs GUI Loop"""
        self.appMainScreen.attributes("-fullscreen",
                                      True)  # "zoomed" is fullscreen except taskbars on startup, "fullscreen" is no taskbars true fullscreen
        self.appMainScreen.bind("<Escape>",
                                lambda event: self.appMainScreen.destroy())  # binds escape key to killing the window
        self.appMainScreen.bind("<F11>",
                                lambda event: self.appMainScreen.attributes("-fullscreen",
                                                                            True))  # switches from zoomed to fullscreen
        self.appMainScreen.bind("<F12>",
                                lambda event: self.appMainScreen.attributes("-fullscreen",
                                                                            False))  # switches from fullscreen to zoomed

        self.appSecondScreen.attributes("-fullscreen",
                                        False)  # "zoomed" is fullscreen except taskbars on startup, "fullscreen" is no taskbars true fullscreen
        self.appSecondScreen.bind("<Escape>", lambda
            event: self.appSecondScreen.destroy())  # binds escape key to killing the window
        self.appSecondScreen.bind("<F11>",
                                  lambda event: self.appSecondScreen.attributes("-fullscreen",
                                                                                True),
                                  lambda event: self.appSecondScreen.geometry(
                                      "1920x1080-1920+0"))  # switches from zoomed to fullscreen
        # self.appSecondScreen.bind("<F11>",
        #                           lambda event: self.appSecondScreen.geometry("1920x1080-1920+0"))  # switches from zoomed to fullscreen

        self.appSecondScreen.bind("<F12>",
                                  lambda event: self.appSecondScreen.attributes("-fullscreen",
                                                                                False))  # switches from fullscreen to zoomed
        self.root.withdraw()

        self.root.mainloop()
        #self.appMainScreen.mainloop()


class Sensors:
    numOfSensors = 0

    def __init__(self, parent, args, SecondScreen, canReceive, graphs):
        # [ Sensor Name, relx ,rely , Reading Xcor Offest , Reading Ycor Offest,  Raw Sensor ID, Converted Sensor ID, labelColor]
        #"High\nPress 1",    0.475, 0.05,  0.0,   0.05, 70, 81, yellow],#, 1, 1],

        self.name, self.relx, self.rely, self.xoff, self.yoff, self.idRaw, self.idConv, self.color = args

        self.canReceive = canReceive
        self.parent = parent
        self.SecondScreen = SecondScreen

        self.idConv = self.idRaw +1
        self.idConvEma = self.idConv + 256
        self.idFake = self.idRaw + 100

        self.sensorData = [0] * 100
        self.GraphStatus = [IntVar() for g in graphs]
        self.index = 0

        # self.dataList = []
        aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        self.label = Label(parent, text=self.name, font=aFont, fg=self.color, bg='black')
        self.label.place(relx=self.relx, rely=self.rely, anchor="nw")
        # Makes label with the reading for its corresponding sensor
        self.ReadingLabel = Label(parent, text="N/A", font=("Verdana", 12), fg='orange', bg='black')
        self.ReadingLabel.place(relx=self.relx + self.xoff, rely=self.rely + self.yoff, anchor="nw")

        self.label2 = Label(SecondScreen, text=self.name, font=aFont, fg=self.color, bg='black')
        self.label2.place(relx=Sensors.numOfSensors % 2 * .1 + .025, rely=(Sensors.numOfSensors // 2) * .075 + .1,
                          anchor="nw")
#         self.RawReadingLabel2 = Label(SecondScreen, text="N/A Raw", font=("Verdana", 9), fg='orange', bg='black')
#         self.RawReadingLabel2.place(relx=Sensors.numOfSensors % 2 * .125 + .025 + .05,
#                                     rely=(Sensors.numOfSensors // 2) * .075 + .05 + .0125, anchor="nw")
        self.ConvReadingLabel2 = Label(SecondScreen, text="N/A Converted", font=("Verdana", 9), fg='orange', bg='black')
        self.ConvReadingLabel2.place(relx=Sensors.numOfSensors % 2 * .1 + .025 + .05,
                                     rely=(Sensors.numOfSensors // 2) * .075 + .1 - .0125, anchor="nw")

        Sensors.numOfSensors += 1

    def resetAll(self, var, label):
        settingID = 0
        DATA = [VERIFICATIONID, self.idRaw, settingID, ]
        CanBusSend(NODEID, DATA)
        label.config(text="Command Sent!", fg="green")

    def setSampleRate(self, var, label):
        val = var.get()
        if isinstance(val, str):
            print(val.upper())
            if val.upper() == "SLOW":
                settingID = 1
                DATA = [VERIFICATIONID, self.idRaw, settingID, ]
                CanBusSend(NODEID, DATA)
            elif val.upper() == "MEDIUM":
                settingID = 2
                DATA = [VERIFICATIONID, self.idRaw, settingID, ]
                CanBusSend(NODEID, DATA)
            elif val.upper() == "Fast":
                settingID = 3
                DATA = [VERIFICATIONID, self.idRaw, settingID, ]
                CanBusSend(NODEID, DATA)

        else:
            print(val)

    def setAlphaEMA(self, var, label):
        settingID = 4
        if self.intTypeCheck(var, int, label, 8):
            binstr = bitstring.BitArray(int=int(var.get()), length=8).bin
            DATA = [VERIFICATIONID, self.idRaw, settingID, int(binstr[0:8], 2)]
            CanBusSend(NODEID, DATA)

    def intTypeCheck(self, var, type, label, size):
        num = var.get()
        if type == int:
            if isint(num):
                try:
                    binstr = bitstring.BitArray(int=int(num), length=size).bin
                    label.config(text="Command Sent!", fg="green")
                    return True
                except bitstring.CreationError as e:
                    label.config(text=e, fg="red")
                    return False
            else:
                label.config(text="Invalid Type.\nInteger Number is required as Input", fg="red")
                return False
        elif type == float:
            if isfloat(num):
                try:
                    binstr = bitstring.BitArray(float=float(num), length=size).bin
                    label.config(text="Command Sent!", fg="green")
                    return True
                except bitstring.CreationError as e:
                    label.config(text=e, fg="red")
                    return False
            else:
                label.config(text="Invalid Type.\nDecimal Value is required as Input", fg="red")
                return False

    # Updates the reading
    # Gets called by the PropulsionFrame class
    def Refresh(self, LabelRefresh):
        value = random.randint(1, 100)
        if CanStatus:
            value = self.canReceive.Sensors[self.idConv]
        self.sensorData = self.sensorData[1:] + self.sensorData[:1]
        self.sensorData[-1] = value
        self.index += 1
        if LabelRefresh:
            self.ReadingLabel.config(fg=orange,text=str(value) + " psi")  # Updates the label with the updated value
            self.ConvReadingLabel2.config(fg=orange,text=str(value) + " psi")
            #self.RawReadingLabel2.config(text=str(self.canReceive.Sensors[self.idRaw]))

class Valves:
    numOfValves = 0

    def __init__(self, parent, args, SecondScreen, canReceive):
        # Name, Relx, Rely , Object ID, HP Channel, Command OFF, Command ON, sensorID, nodeID
        #['HV',   .55,  .25,   16, 2, 34, 35, yellow, 122, 2], 
        name, relx, rely, obj_id, hp_channel, comm_off, comm_on, color, sensorID, nodeID = args
        self.name, self.x_pos, self.y_pos, self.id = name, relx, rely, obj_id
        self.HPChannel, self.commandOFF, self.commandON = hp_channel, comm_off, comm_on
        self.color, self.sensorID, self.nodeID = color, sensorID, nodeID

        self.canReceive = canReceive
        self.parent = parent
        self.SecondScreen = SecondScreen
        self.state = False
        self.photo_name = name
        self.status = 69  # Keeps track of valve actuation state

        self.commandID = 1
        
        if "IGN" in self.photo_name:
            self.photo = "Valve Buttons/" + self.name + "-Off-EnableOn.png"
        else:
            self.photo = "Valve Buttons/" + self.name + "-Closed-EnableOn.png"

        self.photo = Image.open(self.photo).resize((72,72))
        self.photo = ImageTk.PhotoImage(self.photo)
            
        self.Button = Button(parent, font=("Verdana", 10), fg='red', bg='black')
        self.Button.place(relx=self.x_pos, rely=self.y_pos)
        self.Button.config(image=self.photo)
        self.Button.bind('<Double-1>', self.ValveActuation)

        aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        

        self.label2 = Label(SecondScreen, text=self.name, font=aFont, fg=self.color, bg='black')
        self.label2.place(relx=Valves.numOfValves % 2 * .075 + .25,rely=(Valves.numOfValves//2) *.075 + .1, anchor="nw")
        self.StatusLabel2 = Label(SecondScreen, text="N/A Status", font=("Verdana", 9), fg='orange', bg='black')
        self.StatusLabel2.place(relx=Valves.numOfValves % 2 * .075 + .25 + .025,
                                    rely=(Valves.numOfValves//2)* .075 + .1 + .0125,
                                    anchor="nw")
        self.VoltageLabel2 = Label(SecondScreen, text="N/A Voltage", font=("Verdana", 9), fg='orange', bg='black')
        self.VoltageLabel2.place(relx=Valves.numOfValves % 2 * .075 + .25 + .025,
                                     rely=(Valves.numOfValves//2)* .075 + .1 - .0125,
                                     anchor="nw")
        Valves.numOfValves += 1

    def ValveActuation(self, event):
        # User is only allowed to actuate valves if in Test mode
        if Main.CurrState != "Test" and Main.CurrState != "Override":
            return 0
        print(self.name, self.status)
        if self.state:
            DATA = [self.commandOFF]
            CanBusSend(self.commandID, DATA)
        else:

            DATA = [self.commandON]
            CanBusSend(self.commandID, DATA)

    def resetAll(self, var, label):
        settingID = 0
        DATA = [VERIFICATIONID, self.id, settingID]
        CanBusSend(NODEID, DATA)
        label.config(text="Command Sent!", fg="green")

    def setValveType(self, var, label):
        settingID = 1
        val = var.get()
        if isinstance(val, str):
            print(val.upper())
            if val.upper() == "NORMALLY CLOSED":
                DATA = [VERIFICATIONID, self.id, settingID, 0]
                CanBusSend(NODEID, DATA)
            elif val.upper() == "NORMALLY OPEN":
                DATA = [VERIFICATIONID, self.id, settingID, 1]
                CanBusSend(NODEID, DATA)

    def setFullDutyTime(self, var, label):
        settingID = 2
        if self.intTypeCheck(var, int, label, 32):
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setFullDutyCyclePWM(self, var, label):
        settingID = 3
        if self.intTypeCheck(var, int, label, 16):
            binstr = bitstring.BitArray(int=int(var.get()), length=16).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2)]
            CanBusSend(NODEID, DATA)

    def setHoldDutyCyclePWM(self, var, label):
        settingID = 4
        if self.intTypeCheck(var, int, label, 8):
            binstr = bitstring.BitArray(int=int(var.get()), length=8).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2)]
            CanBusSend(NODEID, DATA)

    def setWarmDutyCyclePWM(self, var, label):
        settingID = 5
        if self.intTypeCheck(var, int, label, 16):
            binstr = bitstring.BitArray(int=int(var.get()), length=16).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2)]
            CanBusSend(NODEID, DATA)

    def setLiveOutTime(self, var, label):
        settingID = 1
        if self.intTypeCheck(var, int, label, 32):
            binstr = bitstring.BitArray(int=int(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def intTypeCheck(self, var, type, label, size):
        num = var.get()
        if type == int:
            if isint(num):
                try:
                    binstr = bitstring.BitArray(int=int(num), length=size).bin
                    label.config(text="Command Sent!", fg="green")
                    return True
                except bitstring.CreationError as e:
                    label.config(text=e, fg="red")
                    return False
            else:
                label.config(text="Invalid Type.\nInteger Number is required as Input", fg="red")
                return False
        elif type == float:
            if isfloat(num):
                try:
                    binstr = bitstring.BitArray(float=float(num), length=size).bin
                    label.config(text="Command Sent!", fg="green")
                    return True
                except bitstring.CreationError as e:
                    label.config(text=e, fg="red")
                    return False
            else:
                label.config(text="Invalid Type.\nDecimal Value is required as Input", fg="red")
                return False

    def refresh_valve(self):
        # if self.id in can_receive.node_state and self.status is not can_receive.node_state[self.id]:
        #     self.status = can_receive.node_state[self.id]
        if CanStatus:
            if self.nodeID == 3:
                if self.status == self.canReceive.ValvesRenegadeProp[self.HPChannel]:
                    pass
                self.status = self.canReceive.ValvesRenegadeProp[self.HPChannel]
            if self.nodeID == 2:
                if self.status == self.canReceive.ValvesRenegadeEngine[self.HPChannel]:
                    pass
                self.status = self.canReceive.ValvesRenegadeEngine[self.HPChannel]
            self.VoltageLabel2.config(text = self.canReceive.Sensors[self.sensorID])
            
            if self.status == 0:  # Closed
                self.photo_name = "Valve Buttons/" + self.name + "-Closed-EnableStale.png"
                self.StatusLabel2.config(text  = "Closed")
                self.state = False
            elif self.status == 1:  # Open
                self.photo_name = "Valve Buttons/" + self.name + "-Open-EnableStale.png"
                self.StatusLabel2.config(text  = "Open`")
                self.state = True
            elif self.status == 2:
                self.photo_name = "Valve Buttons/" + self.name + "-FireCommanded-EnableStale.png"
            #             elif can_receive.currRefTime - can_receive.node_state_time[self.id] >= can_receive.staleTimeThreshold:
            #                 self.photo_name = "Valve Buttons/" + self.name + "-Stale-EnableStale.png"
            if not exists(self.photo_name):
                pass
                #print(self.photo_name + " Does not exist. Status is " + str(self.status))
            else:
                #print(self.photo_name, self.status)
                img = Image.open(self.photo_name).resize((72,72))
                self.photo = ImageTk.PhotoImage(img)
                self.Button.config(image=self.photo)


class States:

    # Parent is the Parent Frame
    # args is the data in the States array.
    def __init__(self, parent, args, prevState=None):
        # [ State Name, State ID , commandID, commandOFF , commandON, IfItsAnArmState, StateNumber]
        #["Active",              2, 1,  3,  5, False, 1],
        self.stateName, self.stateID, self.commandID, self.commandOFF, self.commandON, \
            self.isArmState, self.StateNumber = args

        self.parent = parent
        self.state = False
        self.prevState = prevState
        self.relXCor = 0
        self.relYCor = 0
        self.relHeight = 1
        self.relWidth = 1
        self.bgColor = "black"
        self.fontSize = ("Verdana", 10)

    # The Main state buttons get made here
    def MainStateInstantiation(self):
        self.aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        self.relXCor = 0.0125
        self.relHeight = 7/ len(Main.States)/10
        self.relYCor = 1 - (self.relHeight * 1.15) * (len(Main.States) - self.StateNumber + 1) - .025
        self.relWidth = 0.125
        self.bgColor = "black"
        self.isVentAbort = False
        # Goes to logic function when button is pressed
        self.button = Button(self.parent, text=self.stateName, fg='red', bg='black', bd=5,
                             command=lambda: self.Logic(), font=20)  # , font = self.fontSize)
        self.button.place(relx=self.relXCor, rely=self.relYCor, relwidth=self.relWidth, relheight=self.relHeight)

    # The Vent and abort buttons are made here
    def VentAbortInstantiation(self):
        self.relXCor = self.stateID #self.args[1]
        self.relYCor = 0.85
        self.relHeight = .1
        self.relWidth = 1 / 10
        self.bgColor = darkGrey
        self.fontSize = ("Verdana", 26)
        self.isVentAbort = True
        self.button = Button(self.parent, text=self.stateName, command=lambda: self.StateActuation(), fg='red',
                             bg=darkGrey, font=self.fontSize, bd=5)  # , font=self.fontSize)
        self.button.place(relx=self.relXCor, rely=self.relYCor, relheight=self.relHeight, relwidth=self.relWidth)

    # Holds the logic for the state commands and the transition between the states
    # If in Test mode System leaves passive state and cant go into the other states until user has left Test mode
    # The transition between each state can only be done sequentially but Arm states can go back to its previous state
    # If user input follows the specified logic the State Actuaction function is called and it updated the UI buttons

    # Logic for Vent and Abort currently not done
    def Logic(self):
        if self.stateName == "Test":
            if Main.CurrState == "Passive":
                Main.CurrState = "Test"
                self.StateActuation()
            elif Main.CurrState == "Test":
                Main.CurrState = "Passive"
                self.StateActuation()
            else:
                return 0
        elif Main.CurrState != "Test":
            if self.prevState.stateName == Main.CurrState or (
                    Main.CurrState == "Passive" and self.prevState.stateName == "Test"):
                self.StateActuation()
                if self.prevState.stateName != "Test":
                    self.prevState.StateActuation()
                Main.CurrState = self.stateName
            elif Main.CurrState == self.stateName and self.isArmState:
                self.prevState.StateActuation()
                self.StateActuation()
                Main.CurrState = self.prevState.stateName

    # Updates the visuals in the UI to specify whether a state is on or off
    # red if OFF and green if ON
    def StateActuation(self):
        print(self.stateName)
        if self.state:
            self.button.config(fg='red')
            if self.isVentAbort:
                GUI.StateReset()
            self.state = False
            DATA = [self.commandOFF]
            CanBusSend(self.commandID, DATA)
        else:
            self.button.config(fg='green')
            self.state = True
            DATA = [self.commandON]
            CanBusSend(self.commandID, DATA)


class Controller:
    TankControllers = 0

    def __init__(self, args, Screen1, Screen2, canReceive):
        #["Tank Controller HiPress", 2, False, black],
        self.name, self.id, self.isAPropTank, self.color = args
        self.canReceive = canReceive
        self.parentMain = Screen1
        self.parent2 = Screen2
        
        aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        if self.isAPropTank:
            buffer = [
                ["KpLabel",              "Kp",                       .025, 0.525],
                ["KiLabel",              "Ki",                       .075, 0.525],
                ["KdLabel",              "Kd",                       .125, 0.525],
                ["EpLabel",              "Ep",                       .025, 0.6],
                ["EiLabel",              "Ei",                       .075, 0.6],
                ["EdLabel",              "Ed",                       .125, 0.6],
                ["PIDSUMLabel",          "PID SUM",                  .025, 0.7],
                ["TargetValueLabel",     "Target\nValue",            .075, 0.7],
                ["ThresholdLabel",       "Threshold",                .125, 0.7],
                ["EnergizeTime",         "Energize\nTime",           .025, 0.8],
                ["DenergizeTime",        "Denergize\nTime",          .075, 0.8],
                ["VentFailSafePressure", "Vent Fail\nSafe Pressure", .125, 0.8],
            ]

            self.labels = dict()
            for name1, text, relx, rely in buffer:
                self.labels[name1] = Label(self.parent2, fg=self.color, bg=black, font=aFont, text=text)
                self.labels[name1].place(relx=relx + Controller.TankControllers * .2, rely=rely)

                name2 = name1 + '2'
                self.labels[name2] = Label(self.parent2, font=("Verdana", 9), fg='orange', bg='black', text="NA")
                self.labels[name2].place(relx=relx + Controller.TankControllers * .2, rely=rely + 0.05)

            Controller.TankControllers += 1
        if "Engine" in self.name:

            self.Times = dict()

            buffer = [
                ["LOXMVTime",  "LOX MV\nTime (ms)",  blue,  0.45,  0.625, 3],
                ["FuelMVTime", "Fuel MV\nTime (ms)", red,   0.525, 0.625, 2],
                ["IGN1Time",   "IGN 1\nTime (ms)",   green, 0.45,  0.525, 4],
                ["IGN2Time",   "IGN 2\nTime (ms)",   green, 0.525, 0.525, 5],
            ]
            
            for name1, text1, fg, relx, rely, cid in buffer:
                self.Times[name1] = Label(self.parent2, text=text1, fg=fg, bg=black, font=aFont)
                self.Times[name1].place(relx=relx, rely=rely)

                name2 = name1 + '2'
                text2 = str(self.canReceive.Controllers[self.id][cid]/1000)
                self.Times[name2] = Label(self.parent2, text=text2, fg=orange, bg=black, font=("Verdana", 9))
                self.Times[name2].place(relx=relx, rely=rely + 0.05)

        # self.EMA.place(relx=.01, rely=0.575, relwidth=1 / 10, relheight=.02)

        
    def resetAll(self, var, label):
        settingID = 0
        DATA = [VERIFICATIONID, self.id, settingID]
        CanBusSend(NODEID, DATA)
        print("RESET")
        label.config(text="Command Sent!", fg="green")

    def setFuelMVAutosequenceActuation(self, var, label):
        settingID = 1
        if self.intTypeCheck(var, int, label, 32):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8],2), int(binstr[8:16],2), int(binstr[16:24],2), int(binstr[24:32],2)]
            CanBusSend(NODEID, DATA)

    def setLoxMVAutosequenceActuation(self, var, label):
        settingID = 2
        if self.intTypeCheck(var, int, label, 32):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8],2), int(binstr[8:16],2), int(binstr[16:24],2), int(binstr[24:32],2)]
            CanBusSend(NODEID, DATA)

    def setIgniter1ActuationActuation(self, var, label):
        settingID = 3
        if self.intTypeCheck(var, int, label, 32):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8],2), int(binstr[8:16],2), int(binstr[16:24],2), int(binstr[24:32],2)]
            CanBusSend(NODEID, DATA)

    def setIgniter2ActuationActuation(self, var, label):
        settingID = 4
        if self.intTypeCheck(var, int, label, 32):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8],2), int(binstr[8:16],2), int(binstr[16:24],2), int(binstr[24:32],2)]
            CanBusSend(NODEID, DATA)

    def setThrottleProgramPoint(self, time, throttlepoint, label):
        settingID = 5
        if self.intTypeCheck(time, int, label, 16):
            timebin = bitstring.BitArray(int=int(time.get()), length=16).bin
            throttle = bitstring.BitArray(int=int(throttlepoint.get()), length=16).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(timebin[0:8], 2), int(timebin[8:16], 2),
                    int(throttle[0:8], 2), int(throttle[8:16], 2)]
            CanBusSend(NODEID, DATA)

    def throttleProgramReset(self, var, label):
        settingID = 6
        DATA = [VERIFICATIONID, self.id, settingID]
        CanBusSend(NODEID, DATA)
        label.config(text="Command Sent!", fg="green")

    def throttleProgramResetSpecific(self, time, throttlepoint, label):
        settingID = 7
        if self.intTypeCheck(time, int, label, 16):
            binstr = bitstring.BitArray(int=int(time.get()), length=16).bin
            binstr.append(bitstring.BitArray(int=int(throttlepoint.get()), length=16).bin)
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setK_p(self, var, label):
        settingID = 1
        if self.intTypeCheck(var, float, label, 32):
            binstr = bitstring.BitArray(float=float(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setK_i(self, var, label):
        settingID = 2
        if self.intTypeCheck(var, float, label, 32):
            binstr = bitstring.BitArray(float=float(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setK_d(self, var, label):
        settingID = 3
        if self.intTypeCheck(var, float, label, 32):
            binstr = bitstring.BitArray(float=float(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setControllerThreshold(self, var, label):
        settingID = 4
        if self.intTypeCheck(var, float, label, 32):
            binstr = bitstring.BitArray(float=float(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setVentFailsafePressure(self, var, label):
        settingID = 5
        if self.intTypeCheck(var, float, label, 32):
            binstr = bitstring.BitArray(float=float(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setValveMinimumEnergizeTime(self, var, label):
        settingID = 6
        if self.intTypeCheck(var, int, label, 32):
            binstr = bitstring.BitArray(int=int(var.get()), length=32).bin

            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setValveMinimumDeenergizeTime(self, var, label):
        settingID = 7
        if self.intTypeCheck(var, int, label, 32):
            binstr = bitstring.BitArray(int=int(var.get()), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def setCountdownStart(self, var, label):
        settingID = 1
        if self.intTypeCheck(var, int, label, 32):
            var = int(var.get())* 1000
            binstr = bitstring.BitArray(int=int(var), length=32).bin
            DATA = [VERIFICATIONID, self.id, settingID, int(binstr[0:8], 2), int(binstr[8:16], 2),
                    int(binstr[16:24], 2), int(binstr[24:32], 2)]
            CanBusSend(NODEID, DATA)

    def intTypeCheck(self, var, type, label, size):
        num = var.get()
        if type == int:
            if isint(num):
                try:
                    binstr = bitstring.BitArray(int=int(num), length=size).bin
                    label.config(text="Command Sent!", fg="green")
                    return True
                except bitstring.CreationError as e:
                    label.config(text=e, fg="red")
                    return False
            else:
                label.config(text="Invalid Type.\nInteger Number is required as Input", fg="red")
                return False
        elif type == float:
            if isfloat(num):
                try:
                    binstr = bitstring.BitArray(float=float(num), length=size).bin
                    label.config(text="Command Sent!", fg="green")
                    return True
                except bitstring.CreationError as e:
                    label.config(text=e, fg="red")
                    return False
            else:
                label.config(text="Invalid Type.\nDecimal Value is required as Input", fg="red")
                return False

    def Refresh(self):
        if self.isAPropTank:
            if True:#CanStatus:
                self.labels['KpLabel2'].config(             text=      self.canReceive.Controllers[self.id][ 2])
                self.labels['KiLabel2'].config(             text=      self.canReceive.Controllers[self.id][ 3])
                self.labels['KdLabel2'].config(             text=      self.canReceive.Controllers[self.id][ 4])
                self.labels['EpLabel2'].config(             text=round(self.canReceive.Controllers[self.id][ 6]))
                self.labels['EiLabel2'].config(             text=round(self.canReceive.Controllers[self.id][ 8]))
                self.labels['EdLabel2'].config(             text=round(self.canReceive.Controllers[self.id][10]))
                self.labels['PIDSUMLabel2'].config(         text=round(self.canReceive.Controllers[self.id][13]))
                self.labels['TargetValueLabel2'].config(    text=      self.canReceive.Controllers[self.id][12])
                self.labels['ThresholdLabel2'].config(      text=      self.canReceive.Controllers[self.id][ 5])
                self.labels['EnergizeTime2'].config(        text=      self.canReceive.Controllers[self.id][14])
                self.labels['DenergizeTime2'].config(       text=      self.canReceive.Controllers[self.id][15])
                self.labels['VentFailSafePressure2'].config(text=      self.canReceive.Controllers[self.id][16])
        elif "Engine" in self.name:
            self.Times['LOXMVTime2'].config( text=self.canReceive.Controllers[self.id][3]/1000)
            self.Times['FuelMVTime2'].config(text=self.canReceive.Controllers[self.id][2]/1000)
            self.Times['IGN1Time2'].config(  text=self.canReceive.Controllers[self.id][4]/1000)
            self.Times['IGN2Time2'].config(  text=self.canReceive.Controllers[self.id][5]/1000)

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


"""
Starts Code
"""

if CanStatus:
    #canReceive = CanReceive(channel='can0', bustype='socketcan')
    canReceive = CanReceive(channel='virtual', bustype='virtual')

GUI = Main(canReceive)
# GUI.run()
GUIThread = Thread(target=GUI.run)
GUIThread.daemon = True

#
GUIThread.start()
if CanStatus:
    canReceive_thread = Thread(target=canReceive.run)
    canReceive_thread.daemon = True
    canReceive_thread.start()
