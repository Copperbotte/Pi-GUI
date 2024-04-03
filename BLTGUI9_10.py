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
import numpy as np
import config_HRC as HRC

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

class Graph:
    def __init__(self, label, parent, relx, rely, bg=black):
        self.label = label
        self.frame = Canvas(parent, bg=bg)
        self.frame.place(relx=relx, rely=rely, relwidth=.225, relheight=2 / 5)
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvasfigure = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.axis = self.figure.add_subplot()
        self.canvasfigure.get_tk_widget().pack()

class TransformBox:
    def __init__(self,
            origin: tuple[float, float],
            dx:     tuple[float, float],
            dy:     tuple[float, float]):
        self.origin, self.dx, self.dy = tuple(map(np.array, (origin, dx, dy)))
        self.coords = np.array([dx, dy]).T
        self.affine = np.array([dx, dy, origin]).T
        self.transform = np.pad(self.affine, ((0,1), (0,0)), mode='constant', constant_values=0)
        self.transform[-1, -1] = 1

    def __str__(self):
        return str(self.affine)

    def __repr__(self):
        return str(self)
    
    def __call__(self, pts):
        pts = np.array(pts)
        if len(pts.shape) == 1:
            #return self.origin + self.dx*pts[0] + self.dy*pts[1]
            return self.origin + (self.coords @ pts.T).T

        pts = np.pad(pts, ((0,0), (0,1)), mode='constant', constant_values=1)
        #return pts @ self.affine.T
        return (pts @ self.transform.T)[:, :-1]

    def __mul__(self, right):
        res = self.transform @ right.transform
        dx, dy, origin = res[:-1].T
        return TransformBox(origin, dx, dy)

    def asRelArgs(self, pts, anchor='center', **args):
        pts = self(pts)
        res = dict(**args)
        res.update(dict(relx=pts[0], rely=pts[1], anchor=anchor))
        return res

    def asAbsArgs(self, pts, anchor='center', **args):
        pts = self(pts)
        res = dict(**args)
        res.update(dict(x=pts[0], y=pts[1], anchor=anchor))
        return res

    def inv(self):
        dx, dy, origin = np.linalg.inv(self.transform)[:-1].T
        return TransformBox(origin, dx, dy)

class ImageCache:
    def __init__(self):
        self.cache = dict()
    
    def __call__(self, src, resize=None):
        if src not in self.cache:
            self.cache[src] = Image.open(src)
            print("ImageCache: Loaded \"%s\""%src)
            if type(resize) != type(None):
                self.cache[src] = self.cache[src].resize(resize)
            self.cache[src] = ImageTk.PhotoImage(self.cache[src])
        return self.cache[src]

class Main:
    # Data needed to set up the Valve, Sensors, States
    # State LUT Key, VBuffer Index, color
    valves = [
        [HRC.HV_ID,    4, yellow],
        [HRC.HP_ID,    3, yellow],
        [HRC.LDR_ID,  11, blue  ],
        [HRC.FDR_ID,  13, red   ],
        [HRC.LDV_ID,   9, blue  ],
        [HRC.FDV_ID,  15, red   ],
        [HRC.LV_ID,   16, blue  ],
        [HRC.FV_ID,   19, red   ],
        [HRC.LMV_ID,  26, blue  ],
        [HRC.FMV_ID,  29, red   ],
        [HRC.IGN1_ID, 34, green ],
        [HRC.IGN2_ID, 35, green ]
    ]
    # [ 
    # Sensor LUT Key, Grid Key, Grid Position, Box Position, Box Adj, Color
    sensors = [
        [HRC.PT_LOX_HIGH_ID,      "HiPr", (  0,   0), (1, 0), (0, 1/3), yellow],
        [HRC.PT_FUEL_HIGH_ID,     "HiPr", (  1,   0), (0, 0), (0, 1/3), yellow],

        [HRC.PT_FUEL_TANK_1_ID,   "Fuel", (  0,   0), (0, 1), (0, 1/3), red   ],
        [HRC.PT_FUEL_DOME_ID,     "Fuel", (  0,   1), (0, 2), (0, 1/3), red   ],
        [HRC.PT_FUEL_TANK_2_ID,   "Fuel", (  1,   0), (0, 3), (0, 1/3), red   ],
        [HRC.PT_FUEL_INLET_ID,    "Fuel", (  1,   1), (0, 4), (0, 1/3), red   ],
        [HRC.PT_FUEL_INJECTOR_ID, "Fuel", (1/2,   2), (0, 5), (0, 1/3), red   ],

        [HRC.PT_LOX_DOME_ID,      "Loxy", (  0,   1), (1, 1), (0, 1/3), blue  ],
        [HRC.PT_LOX_TANK_1_ID,    "Loxy", (  1,   0), (1, 2), (0, 1/3), blue  ],
        [HRC.PT_LOX_TANK_2_ID,    "Loxy", (  0,   0), (1, 3), (0, 1/3), blue  ],
        [HRC.PT_LOX_INLET_ID,     "Loxy", (  1,   1), (1, 4), (0, 1/3), blue  ],
        
        [HRC.PT_CHAMBER_1_ID,     "Yeet", (  0,   0), (0, 6), (0, 1/3), green ],
        [HRC.PT_CHAMBER_2_ID,     "Yeet", (  1,   0), (0, 7), (0, 1/3), green ],
        [HRC.PT_PNUEMATICS_ID,    "Aero", (  0,   0), (0, 8), (0, 1/3), purple],

       #[HRC.PT_LOAD_CELL_1_ID,   "Yeet", (  0,   1), (1, 5), (0, 1/3), green ],
       #[HRC.PT_LOAD_CELL_2_ID,   "Yeet", (  1,   1), (1, 6), (0, 1/3), green ],
       #[HRC.PT_LOAD_CELL_3_ID,   "Yeet", (1/2, 3/2), (1, 7), (0, 1/3), green ],
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
        "Abort", .265, 1, 3, 7, False, 0
    ]
    Controllers = [
        #["Tank Controller HiPress", 2, False, yellow],
        #["Tank Controller Lox",     3, True,  blue ],  # Unused features
        #["Tank Controller Fuel",    4, True,  red  ],
        #["Engine Controller 1",      5, False, black],
        ##["Auto Sequence",            1, False, black],
        ##["Node Controller",          0, False, black],
    ]

    # System starts off in a passive state
    CurrState = "Passive"

    def __init__(self, canReceive, canSend):
        self.canReceive = canReceive
        self.canSend = canSend

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
            ["GUI Images/Engine_Clipart.png",        32],
            ["GUI Images/LOxTankClipart.png",        20],
            ["GUI Images/FuelTankClipart.png",       24],
            ["GUI Images/PressurantTankClipart.png",  0]
        ]

        tf = self.boxWireGrid

        for src, i in buffer:
            img = self.imageCache(src)
            label = Label(self.parentMainScreen, image=img, bg=black)
            label.image = img
            label.place(**self.boxWireGrid.asAbsArgs(self.Vertex_Buffer[i]))
        
    def propLinePlacement(self):
        # Lines showing the fluid flow routing in the fluid system
        aFont = tkFont.Font(family="Verdana", size=15, weight="bold")

        self.Vertex_Buffer = \
        Vertex_Buffer = [ 
            (  0,  1),
            (  0,  5), ( 12,  5), ( 16,  5), ( 12, 10),
            ( -8,  8), (  0,  8), (  8,  8),
            
            (  0, 11),
            (-12, 14), ( -8, 14), ( -4, 14), (  0, 14), ( 4, 14), (  8, 14), ( 12, 14),

            (-12, 18), ( -8, 18), (  8, 18), ( 12, 18),
            ( -8, 23), ( -4, 22), (  0, 22), (  4, 22), (  8, 23), 
            
            ( -8, 28), ( -4, 28), (-.6, 28), ( .6, 28), (  4, 28), (  8, 28),
            (-.6, 34), (  0, 34), ( .6, 34),
            
            ( 4, 32), ( 4, 35)
        ]
        # One of these vertices is unused, and a lot are unneeded.
        # They're used for positioning of valve buttons later.

        ScreenSpace = TransformBox((800,  50), (25, 0), (0, 25))
        self.boxWireGrid = self.boxWireGrid * ScreenSpace

        Color_Buffer = [yellow, purple, blue, red]

        Index_Buffer = [
            # High Pressure lines
            ( 0,  0,  1,  6,  8),
            ( 0,  1,  2,  3),
            ( 0,  2,  4),
            ( 0, 10,  5,  6,  7, 14),
            
            # Pnumatics
            ( 1,  8, 12, 22),
            ( 1,  9, 10, 11, 12, 13, 14, 15),
            ( 1, 26, 21, 22, 23, 29),

            # Lox
            ( 2, 10, 17, 20, 25, 26, 27, 31),
            ( 2, 16, 17),

            # Fuel
            ( 3, 14, 18, 24, 30, 29, 28, 33),
            ( 3, 18, 19)
        ]

        #self.WireDebugNumbers = []
        #for i, v in enumerate(Vertex_Buffer):
        #    self.WireDebugNumbers.append(Label(self.parentMainScreen, fg=orange, bg=black, font=aFont, text="%d"%i))
        #    self.WireDebugNumbers[-1].place(**self.boxWireGrid.asAbsArgs(v))

        for inds in Index_Buffer:
            color = Color_Buffer[inds[0]]
            verts = tuple(map(lambda i: self.boxWireGrid(Vertex_Buffer[i]).tolist(), inds[1:]))
            self.parentMainScreen.create_line(*verts, fill=color, width=5, capstyle='round')
            for i,v in zip(inds[1:], verts):
                self.parentMainScreen.create_line(v, v, fill=color, width=10, capstyle='round')
                #self.WireDebugNumbers.append(Label(self.parentMainScreen, fg=color, bg=black, font=aFont, text="%d"%i))
                #self.WireDebugNumbers[-1].place(x=v[0], y=v[1], anchor='center')
        
        # This holds the control buttons on the left.
        self.parentMainScreen.create_rectangle(10, 160, 275, 1020, outline=orange, fill=black, width=5)

        # Second display SENSORS box
        self.SensorsLabel = Label(self.parentSecondScreen, fg=orange, bg=black, font=aFont, text="SENSORS")
        self.SensorsLabel.place(**self.boxSensorGrid.asAbsArgs((1/2, -2/3)))

        # Second display VALVES box
        self.ValvesLabel = Label(self.parentSecondScreen, fg=orange, bg=black, font=aFont, text="VALVES")
        self.ValvesLabel.place(**self.boxValveGrid.asAbsArgs((1/2, -2/3)))
        
        # Second display ENGINE CONTROLLER box
        self.FuelControllerLabel = Label(self.parentSecondScreen, fg=green, bg=black, font=aFont, text="ENGINE CONTROLLER")
        self.FuelControllerLabel.place(**self.boxEngineControllerGrid.asAbsArgs((1/2, -2/3)))

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
            img = self.imageCache("GUI Images/ManualOverrideDisabledButton.png")
            self.Button = Button(self.parentMainScreen, image=img, fg='red', bg='black', bd=5)
            self.parentMainScreen.killSwitchState = False
            self.reminderButtonOfCurrState.destroy()
            Main.CurrState = self.savedCurrState
            # msg = can.Message(arbitration_id=self.overrideCommandID, data=[self.overrideCommandON], is_extended_id=False)
            # bus.send(msg)
        else:
            img = self.imageCache("GUI Images/ManualOverrideEnabledButton.png")
            self.Button = Button(self.parentMainScreen, image=img, fg='green', bg='black', bd=5)
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

            #self.autosequence_str = "T  " + str(self.canReceive.AutosequenceTime) + " s"
            #self.autoseqence.config(text=self.autosequence_str)
            self.time.config(text=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            #self.nodeState.config(text=self.canReceive.NodeStatus)  # can_receive.node_dict_list[self.name]["state"]))

            self.sensorList[1].ReadingLabel.after(GRAPHDATAREFRESHRATE, self.Refresh)
        else:
            for sensor in self.sensorList:
                sensor.Refresh(False)
                self.refreshCounter += GRAPHDATAREFRESHRATE

            self.sensorList[1].ReadingLabel.after(GRAPHDATAREFRESHRATE, self.Refresh)
            
        #self.EngineNodeState.config(text = "Engine Node State: " + self.canReceive.NodeStatusRenegadeEngine)
        #self.PropNodeState.config(text = "Prop Node State: " + self.canReceive.NodeStatusRenegadeProp)
        self.EngineNodeState.config(text="Engine Node State: " + HRC.StateLUT[self.canReceive.rocketState[HRC.SR_ENGINE]])
        self.PropNodeState.config(  text="Prop Node State: "   + HRC.StateLUT[self.canReceive.rocketState[HRC.SR_PROP]])

    def StateReset(self):
        Main.CurrState = "Passive"
        # Store previosly instantiated State. Arm States may be able to access the state before it
        prevState = None
        # Every state in State Array gets instantiated and a Button is made for it
        for i in range(len(Main.States)):
            button = States(self.parentMainScreen, Main.States[i], self.canSend, prevState=prevState)
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

    def GenerateBoxes(self):
        #self.GridScale = TransformBox((0, 0), (1920,0), (0,1041))

        # This was learned using gradient descent on the difference of the original transform on valveList, and 
        # pts2 = np.array([[v.StatusLabel2.winfo_x(), v.StatusLabel2.winfo_y()] for v in GUI.valveList]).
        #self.GridScale = TransformBox((24,-23), (1920,0), (0,1040))
        #self.GridScale = TransformBox((0,0), (1920,0), (0,1040))
        # 
        # The above commented out code was used to find relative positioned coordinates.
        #     I've since moved to absolute coordinates, since the pi's target displays shouldn't ever change.
        #     Feel free to remove this comment block as needed. -Joe Kesser, 2024 March 28

        self.GridScale = TransformBox((0,0), (1920,0), (0,1080))
        self.boxWireGrid = TransformBox(self.GridScale((-0.025, 0)), (1,0), (0,1))
        
        boxSensorGrid = TransformBox((0.025+0.035, 0.100 + 0.015), (0.1, 0), (0, 0.075))
        boxValveGrid = TransformBox(boxSensorGrid((2,0)), (0.075, 0), (0, 0.075))
        boxEngineControllerGrid = TransformBox(boxValveGrid((0,7 + 2/5)), (0.075,0), (0,0.1))
        
        self.boxSensorGrid = self.GridScale * boxSensorGrid
        self.boxValveGrid = self.GridScale * boxValveGrid
        self.boxEngineControllerGrid = self.GridScale * boxEngineControllerGrid

        # Main display boxes
        boxLoxGrid = TransformBox((0.175+0.01, 0.6), (0.05, 0), (0, 0.1))
        boxEngineGrid = TransformBox((0.55+0*0.025, 0.588), (0.05, 0), (0, 0.1))
        
        boxFuelGrid = TransformBox(boxEngineGrid((2.5,0)), (0.05, 0), (0, 0.1))
        
        boxAeroGrid = TransformBox((0.39, 0.62), (0.05, 0), (0, 0.1))
        boxHighPress = TransformBox((0.475, 0.075), (0.05, 0), (0, 0.1))
        
        self.boxLoxGrid = self.GridScale * boxLoxGrid
        self.boxEngineGrid = self.GridScale * boxEngineGrid
        self.boxFuelGrid = self.GridScale * boxFuelGrid
        self.boxAeroGrid = self.GridScale * boxAeroGrid
        self.boxHighPress = self.GridScale * boxHighPress

        self.dictBoxGridsMain = dict(
            Loxy=self.boxLoxGrid,
            Yeet=self.boxEngineGrid,
            Fuel=self.boxFuelGrid,
            Aero=self.boxAeroGrid,
            HiPr=self.boxHighPress
        )

    def GenerateBoxDebug(self):

        boxSensorGrid = self.GridScale * self.boxSensorGrid
        boxValveGrid = self.GridScale * self.boxValveGrid

        pts = np.array([[0,0], [1,0], [1,1], [0,1], [0,0]])

        buffer = [
            # Display 1 Boxes
            [0, self.boxLoxGrid,    (-2/3, -1/2), 2+1/3, 2,     1, blue],
            [0, self.boxEngineGrid, (-2/3, -1/2), 2+1/3, 2+1/3, 1, green],
            [0, self.boxFuelGrid,   (-2/3, -1/2), 2+1/3, 3,     1, red],
            [0, self.boxAeroGrid,   (-2/3, -1/2), 1+1/3, 1,     1, purple],
            [0, self.boxHighPress,  (-2/3, -1/2), 2+1/3, 1,     1, yellow],

            # Display 2 Boxes
            [1, self.boxSensorGrid,           (-0.5,-1.25), 2, 10,   5, orange],
            [1, self.boxValveGrid,            (-0.5,-1.25), 2, 7,    5, orange],
            [1, self.boxEngineControllerGrid, (-0.5,-1),    2, 2.5,  5, green],
        ]

        displays = [self.parentMainScreen, self.parentSecondScreen]
        
        for di, tf, pt, dx, dy, width, color in buffer:
            tf = tf * TransformBox(pt, (dx,0), (0,dy))
            displays[di].create_line(*tf(pts).tolist(), fill=color, width=width, joinstyle='miter')

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
            "Live Out Time":        self.chosenValve.setLiveOutTime,
        }
        if Function == "Reset":
            self.ValveSetDataEntry.destroy()
        
        if Function in fptr:
            self.ValveDataEntryButton.config(
                command=lambda: fptr[Function](self.ValveSetData, self.ValveStatusLabel)
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
        self.canSend(1, DATA)

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

        self.imageCache = ImageCache()

        self.aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        
        self.PropNodeState = Label(self.parentMainScreen, text="Prop Node State", fg=orange, bg=black, font=("Arial", 25))
        self.PropNodeState.place(relx=.01, rely=0.02)
        self.EngineNodeState = Label(self.parentMainScreen, text="Engine Node State", fg=orange, bg=black, font=("Arial", 25))
        self.EngineNodeState.place(relx=.01, rely=0.07)

        self.GenerateBoxes()
        self.propLinePlacement()
        self.imagePlacement()
        self.AutoSequence()
        self.StateReset()
        self.GenerateGraphs()
        self.GenerateBoxDebug()
        

        self.Vent = States(self.parentMainScreen, Main.Vent, self.canSend)
        self.Vent.VentAbortInstantiation()
        self.Abort = States(self.parentMainScreen, Main.Abort, self.canSend)
        self.Abort.VentAbortInstantiation()
        # Instantiates Every Valve
        for valve in Main.valves:
            self.valveList.append(Valves(self.parentMainScreen, valve, self.parentSecondScreen, self.canReceive, self.canSend, self.boxValveGrid, self.boxWireGrid, self.Vertex_Buffer, self.imageCache))

        # Instantiates Every Sensor
        for sensor in Main.sensors:
            self.sensorList.append(Sensors(self.parentMainScreen, sensor, self.parentSecondScreen, self.canReceive, self.canSend, self.graphs, self.boxSensorGrid, self.dictBoxGridsMain))

        # Instantiates Every Sensor
        for controller in Main.Controllers:
            self.controllerList.append(Controller(controller, self.parentMainScreen, self.parentSecondScreen, self.canReceive, self.canSend, self.boxEngineControllerGrid, self.GridScale))

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

        #self.GenerateBoxDebug()

        self.root.mainloop()
        #self.appMainScreen.mainloop()


class Sensors:
    numOfSensors = 0

    def __init__(self, parent, args, SecondScreen, canReceive, canSend, graphs, boxSensorGrid, dictBoxGridsMain):
        # Sensor LUT Key, Grid Key, Grid Position, Box Position, Box Adj, Color
        # [HRC.PT_LOX_HIGH_ID,      "HiPr", (  0,   0), (1, 0), (0, 1/3), yellow],

        self.id, self.grid, self.xy0, self.xy1, self.xyoff, self.color = args

        self.canReceive = canReceive
        self.canSend = canSend
        self.parent = parent
        self.SecondScreen = SecondScreen

        self.sensorData = [0] * 100
        self.GraphStatus = [IntVar() for g in graphs]
        self.index = 0

        self.name = HRC.SensorLUT[self.id]['name']
        self.xy0, self.xy1, self.xyoff = tuple(map(np.array, [self.xy0, self.xy1, self.xyoff]))

        # self.dataList = []
        aFont = tkFont.Font(family="Verdana", size=10, weight="bold")

        placeargs = dict(anchor="center") # dict(anchor="nw")
        bg = black#purple if self.numOfSensors == 0 else black


        ### 1st Display
        pt = np.array(self.xy0)
        adj = TransformBox(pt, (1/2,0), (0,1/2))
        tf = dictBoxGridsMain[self.grid] * adj
        
        # self.label corresponds with the main screen box labels, as their titles.
        self.label = Label(parent, text=self.name, font=aFont, fg=self.color, bg=bg)
        self.label.place(**tf.asAbsArgs(-self.xyoff))
        
        # self.ReadingLabel is the corresponding value for this box.
        self.ReadingLabel = Label(parent, text="N/A", font=("Verdana", 12), fg=orange, bg=bg)
        self.ReadingLabel.place(**tf.asAbsArgs(self.xyoff))

        # Draws the background box
        pts = np.array([[-1, -1], [-1, 1], [1,1], [1,-1], [-1,-1]])
        tf = tf * TransformBox((0,0), (6/7,0), (0,1/3))
        parent.create_line(*tf(pts).tolist(), fill=self.color, width=1, capstyle='projecting', joinstyle='miter')

        
        ### 2nd Display
        #pt = np.array([Sensors.numOfSensors % 2, Sensors.numOfSensors // 2])
        pt = np.array(self.xy1)
        adj = TransformBox(pt, (1/5,0), (0,1))
        tf = boxSensorGrid * adj
        
        pt0 = tf.asAbsArgs((-1, 0))
        pt1 = tf.asAbsArgs(( 1, 0))

        # self.label2 is the sensor title in the SENSORS box.
        self.label2 = Label(SecondScreen, text=self.name, font=aFont, fg=self.color, bg=bg)
        self.label2.place(**pt0)
#         self.RawReadingLabel2 = Label(SecondScreen, text="N/A Raw", font=("Verdana", 9), fg='orange', bg=bg)
#         self.RawReadingLabel2.place(relx=Sensors.numOfSensors % 2 * .125 + .025 + .05,
#                                     rely=(Sensors.numOfSensors // 2) * .075 + .05 + .0125, **placeargs)
        
        # self.ConvReadingLabel2 is the corresponding value for this box.
        self.ConvReadingLabel2 = Label(SecondScreen, text="N/A Converted", font=("Verdana", 9), fg='orange', bg=bg)
        self.ConvReadingLabel2.place(**pt1)

        # Draws the background box
        pts = np.array([[-1, -1], [-1, 1], [1,1], [1,-1], [-1,-1]])
        tf = tf * TransformBox((0,0), (1,0), (0,1/3))
        SecondScreen.create_line(*tf(pts).tolist(), fill=self.color, width=1, capstyle='projecting', joinstyle='miter')

        Sensors.numOfSensors += 1

    # Updates the reading
    # Gets called by the PropulsionFrame class
    def Refresh(self, LabelRefresh):
        value = random.randint(1, 100)
        if CanStatus:
            value = self.canReceive.Sensor_Val[self.id]
        self.sensorData = self.sensorData[1:] + self.sensorData[:1]
        self.sensorData[-1] = value
        self.index += 1
        if LabelRefresh:
            # The first call are to the main display boxes,
            # the second call is to the Sensors box.
            self.ReadingLabel.config(fg=orange, text=str(value) + " psi")  # Updates the label with the updated value
            self.ConvReadingLabel2.config(fg=orange, text=str(value) + " psi")
            #self.RawReadingLabel2.config(text=str(self.canReceive.Sensors[self.idRaw]))


    def resetAll(self, var, label):
        self.canSend.sensor_resetAll(self.idRaw)
        label.config(text="Command Sent!", fg="green")

    def setSampleRate(self, var, label):
        mode = self.canSend.sensor_setSampleRate(self.idRaw, var.get())
        print(mode)

    def setAlphaEMA(self, var, label):
        self.canSend.sensor_setAlphaEMA(self.idRaw, var, label)

class Valves:
    numOfValves = 0
    gui_state_offset = 4096

    def imgFromState(self):
        status = self.StatusStates[self.status] 
        enable = self.EnableStates[self.enable]
        select = '-'.join([self.photo_name, status, enable])
        return self.imageCache("Valve Buttons/%s.png"%select, resize=(72,72))

    def __init__(self, parent, args, SecondScreen, canReceive, canSend, boxValveGrid, boxWireGrid, Vertex_Buffer, imageCache):
        # State LUT Key, VBuffer Index, color
        # [HRC.HV_ID,    4, yellow],

        self.id, self.index, self.color = args

        self.canReceive = canReceive
        self.canSend = canSend
        self.imageCache = imageCache
        self.parent = parent
        self.SecondScreen = SecondScreen
        self.state = False
        self.nick = HRC.ToggleLUT[self.id]['nick']
        self.photo_name = self.nick.replace(' ','')
        self.status = 69  # Keeps track of valve actuation state

        self.commandID = 1

        aFont = tkFont.Font(family="Verdana", size=10, weight="bold")

        placeargs = dict(anchor="nw") # dict(anchor="center")
        bg = black#purple if self.numOfSensors == 0 else black
        
        # Precache valve photos
        # LP and FP do not have stale states.
        # Do those valves still exist?
        lut = HRC.ToggleLUT[self.id]
        self.StatusStates = {k:v for k,v in zip(lut['states'], lut['statestr'])}
        self.StatusStates[lut['states'][0]+self.gui_state_offset] = "FireCommanded"
        self.StatusStates[lut['states'][1]+self.gui_state_offset] = "Stale"
        self.EnableStates = {i:e for i,e in enumerate(["EnableOff", "EnableOn", "EnableStale"])}

        #for status in self.StatusStates:
        #    for enable in self.EnableStates:
        #        self.status, self.enable = status, enable
        #        self.imgFromState()

        self.status, self.enable = max(self.StatusStates), 2
        self.photo = self.imgFromState()

        # Displays a button on a vertex in the propline diagram.
        self.Button = Button(parent, font=("Verdana", 10), fg=red, bg=bg)
        self.Button.place(**boxWireGrid.asAbsArgs(Vertex_Buffer[self.index]))
        self.Button.config(image=self.photo)
        self.Button.bind('<Double-1>', self.ValveActuation)

        # Displays valve info on the 2nd display
        pt = np.array([Valves.numOfValves % 2, Valves.numOfValves // 2])
        adj = TransformBox(pt, (1/6,0), (0,1/6))
        tf = boxValveGrid * adj

        pt0 = tf.asAbsArgs((-1, 0))
        pt1 = tf.asAbsArgs(( 1,-1))
        pt2 = tf.asAbsArgs(( 1, 1))

        self.label2 = Label(SecondScreen, text=self.nick, font=aFont, fg=self.color, bg=bg)
        self.label2.place(**pt0)
        self.StatusLabel2 = Label(SecondScreen, text="N/A Status", font=("Verdana", 9), fg=orange, bg=bg)
        self.StatusLabel2.place(**pt1)
        self.VoltageLabel2 = Label(SecondScreen, text="N/A Voltage", font=("Verdana", 9), fg=orange, bg=bg)
        self.VoltageLabel2.place(**pt2)

        # Draws the background box
        pts = np.array([[-1, -1], [-1, 1], [1,1], [1,-1], [-1,-1]])
        SecondScreen.create_line(*tf(pts).tolist(), fill=self.color, width=1, capstyle='projecting', joinstyle='miter')
        
        Valves.numOfValves += 1

    def ValveActuation(self, event):
        # User is only allowed to actuate valves if in Test mode
        if Main.CurrState != "Test" and Main.CurrState != "Override":
            return
        
        if self.gui_state_offset < self.status:
            return

        # Request to toggle state
        fptr = {
            HRC.IGN1_ID: [ self.canSend.ign1_off,  self.canSend.ign1_on],
            HRC.IGN2_ID: [ self.canSend.ign2_off,  self.canSend.ign2_on],
              HRC.HP_ID: [ self.canSend.hp_close,  self.canSend.hp_open],
              HRC.HV_ID: [ self.canSend.hv_close,  self.canSend.hv_open],
             HRC.FMV_ID: [self.canSend.fmv_close, self.canSend.fmv_open],
             HRC.LMV_ID: [self.canSend.lmv_close, self.canSend.lmv_open],
              HRC.LV_ID: [ self.canSend.lv_close,  self.canSend.lv_open],
             HRC.LDV_ID: [self.canSend.ldv_close, self.canSend.ldv_open],
             HRC.LDR_ID: [self.canSend.ldr_close, self.canSend.ldr_open],
              HRC.FV_ID: [ self.canSend.fv_close,  self.canSend.fv_open],
             HRC.FDV_ID: [self.canSend.fdv_close, self.canSend.fdv_open],
             HRC.FDR_ID: [self.canSend.fdr_close, self.canSend.fdr_open],
        }

        # Reverses the state-function mapping
        states = HRC.ToggleLUT[self.id]['states']
        smap = {k:v for k,v in zip(states, reversed(states))}
        target = smap[self.status]
        self.enable = states.index(target)

        print(self.nick, self.status, self.StatusStates[self.status], "Calling:", fptr[self.id][self.enable].__name__)
        fptr[self.id][self.enable]()

        self.refresh_valve()

    def resetAll(self, var, label):
        self.canSend.valve_resetAll(self.id)
        label.config(text="Command Sent!", fg="green")

    def setValveType(self, var, label):
        self.canSend.valve_setValveType(self.id, var.get())

    def setFullDutyTime(self, var, label):
        self.canSend.valve_setFullDutyTime(self.id, var, label)

    def setFullDutyCyclePWM(self, var, label):
        self.canSend.valve_setFullDutyCyclePWM(self.id, var, label)

    def setHoldDutyCyclePWM(self, var, label):
        self.canSend.valve_setHoldDutyCyclePWM(self.id, var, label)

    def setWarmDutyCyclePWM(self, var, label):
        self.canSend.valve_setWarmDutyCyclePWM(self.id, var, label)

    def setLiveOutTime(self, var, label):
        self.canSend.valve_setLiveOutTime(self.id, var, label)

    def refresh_valve(self):
        # if self.id in can_receive.node_state and self.status is not can_receive.node_state[self.id]:
        #     self.status = can_receive.node_state[self.id]
        if CanStatus:
            #if self.nodeID == 3:
            #    self.status = self.canReceive.ValvesRenegadeProp[self.HPChannel]
            #if self.nodeID == 2:
            #    self.status = self.canReceive.ValvesRenegadeEngine[self.HPChannel]
            self.status = self.canReceive.States[self.id]
            #self.VoltageLabel2.config(text = self.canReceive.Sensors[self.sensorID])
            self.VoltageLabel2.config(text='N/A Volts')
            
            self.StatusLabel2.config(text=self.StatusStates[self.status])
            self.photo = self.imgFromState()
            self.Button.config(image=self.photo)

            """
            if self.status == 0:  # Closed
                src = "Valve Buttons/" + self.photo_name + "-Closed-EnableStale.png"
                self.StatusLabel2.config(text  = "Closed")
                self.state = False
            elif self.status == 1:  # Open
                src = "Valve Buttons/" + self.photo_name + "-Open-EnableStale.png"
                self.StatusLabel2.config(text  = "Open`")
                self.state = True
            elif self.status == 2:
                src = "Valve Buttons/" + self.photo_name + "-FireCommanded-EnableStale.png"
            #             elif can_receive.currRefTime - can_receive.node_state_time[self.id] >= can_receive.staleTimeThreshold:
            #                 self.photo_name = "Valve Buttons/" + self.name + "-Stale-EnableStale.png"
            else:
                if "IGN" in self.photo_name:
                    src = "Valve Buttons/" + self.photo_name + "-Off-EnableOn.png"
                else:
                    src = "Valve Buttons/" + self.photo_name + "-Closed-EnableOn.png"
            if not exists(src):
                pass
                #print(self.photo_name + " Does not exist. Status is " + str(self.status))
            else:
                #print(self.photo_name, self.status)
                self.photo = self.imageCache(src, resize=(72,72))
                self.Button.config(image=self.photo)
            """


class States:

    # Parent is the Parent Frame
    # args is the data in the States array.
    def __init__(self, parent, args, canSend, prevState=None):
        # [ State Name, State ID , commandID, commandOFF , commandON, IfItsAnArmState, StateNumber]
        #["Active",              2, 1,  3,  5, False, 1],
        self.stateName, self.stateID, self.commandID, self.commandOFF, self.commandON, \
            self.isArmState, self.StateNumber = args

        self.parent = parent
        self.state = False
        self.prevState = prevState
        self.canSend = canSend
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
        else:
            self.button.config(fg='green')
            self.state = True
        #self.canSend.state_StateActuation(self.commandID, self.state, self.commandOFF, self.commandON)


class Controller:
    TankControllers = 0

    def __init__(self, args, Screen1, Screen2, canReceive, canSend, boxEngineControllerGrid, GridScale):
        #["Tank Controller HiPress", 2, False, black],
        self.name, self.id, self.isAPropTank, self.color = args
        self.canReceive = canReceive
        self.canSend = canSend
        self.parentMain = Screen1
        self.parent2 = Screen2
        
        aFont = tkFont.Font(family="Verdana", size=10, weight="bold")
        if self.isAPropTank:
            buffer = [
                ["KpLabel",              "Kp",                       0, 0],
                ["KiLabel",              "Ki",                       1, 0],
                ["KdLabel",              "Kd",                       2, 0],
                ["EpLabel",              "Ep",                       0, 1],
                ["EiLabel",              "Ei",                       1, 1],
                ["EdLabel",              "Ed",                       2, 1],
                ["PIDSUMLabel",          "PID SUM",                  0, 2],
                ["TargetValueLabel",     "Target\nValue",            1, 2],
                ["ThresholdLabel",       "Threshold",                2, 2],
                ["EnergizeTime",         "Energize\nTime",           0, 3],
                ["DenergizeTime",        "Denergize\nTime",          1, 3],
                ["VentFailSafePressure", "Vent Fail\nSafe Pressure", 2, 3],
            ]

            tf0 = GridScale * TransformBox((0.5, Controller.TankControllers/3), (1, 0), (0, 1)) * TransformBox((.025, 0.25), (0.05, 0), (0, 0.075))

            self.labels = dict()
            for name1, text, relx, rely in buffer:

                pt = np.array([relx, rely])
                adj = TransformBox(pt, (1/3,0), (0,1/6))
                tf = tf0 * adj
                
                self.labels[name1] = Label(self.parent2, fg=self.color, bg=black, font=aFont, text=text)
                self.labels[name1].place(**tf.asAbsArgs((0, -1)))

                name2 = name1 + '2'
                self.labels[name2] = Label(self.parent2, font=("Verdana", 9), fg='orange', bg='black', text="NA")
                self.labels[name2].place(**tf.asAbsArgs((0, 1)))

            Controller.TankControllers += 1
        if "Engine" in self.name:

            self.Times = dict()

            buffer = [
                ["LOXMVTime",  "LOX MV\nTime (ms)",  blue,  0, 1, 3],
                ["FuelMVTime", "Fuel MV\nTime (ms)", red,   1, 1, 2],
                ["IGN1Time",   "IGN 1\nTime (ms)",   green, 0, 0, 4],
                ["IGN2Time",   "IGN 2\nTime (ms)",   green, 1, 0, 5],
            ]
            
            for name1, text1, fg, relx, rely, cid in buffer:
                pt = np.array([relx, rely])
                adj = TransformBox(pt, (1/3,0), (0,1/6))
                tf = boxEngineControllerGrid * adj
                
                self.Times[name1] = Label(self.parent2, text=text1, fg=fg, bg=black, font=aFont)
                self.Times[name1].place(**tf.asAbsArgs((0, -1)))

                name2 = name1 + '2'
                text2 = str(self.canReceive.Controllers[self.id][cid]/1000)
                self.Times[name2] = Label(self.parent2, text=text2, fg=orange, bg=black, font=("Verdana", 9))
                self.Times[name2].place(**tf.asAbsArgs((0, 1)))

                # Draws the background box
                pts = np.array([[-1, -1], [-1, 1], [1,1], [1,-1], [-1,-1]])
                Screen2.create_line(*tf(pts).tolist(), fill=fg, width=1, capstyle='projecting', joinstyle='miter')

        # self.EMA.place(relx=.01, rely=0.575, relwidth=1 / 10, relheight=.02)
        
    def resetAll(self, var, label):
        self.canSend.controller_resetAll(self.id)
        print("RESET")
        label.config(text="Command Sent!", fg="green")

    def setFuelMVAutosequenceActuation(self, var, label):
        self.canSend.controller_setFuelMVAutosequenceActuation(self.id, var, label)

    def setLoxMVAutosequenceActuation(self, var, label):
        self.canSend.controller_setLoxMVAutosequenceActuation(self.id, var, label)

    def setIgniter1ActuationActuation(self, var, label):
        self.canSend.controller_setIgniter1ActuationActuation(self.id, var, label)

    def setIgniter2ActuationActuation(self, var, label):
        self.canSend.controller_setIgniter2ActuationActuation(self.id, var, label)

    def setThrottleProgramPoint(self, time, throttlepoint, label):
        self.canSend.controller_setThrottleProgramPoint(self.id, time, throttlepoint, label)

    def throttleProgramReset(self, var, label):
        self.canSend.controller_throttleProgramReset(self.id)
        label.config(text="Command Sent!", fg="green")

    # This one is too different to generalize.
    def throttleProgramResetSpecific(self, time, throttlepoint, label):
        self.canSend.controller_throttleProgramResetSpecific(self.id, time, throttlepoint, label)

    def setK_p(self, var, label):
        self.canSend.controller_setK_p(self.id, var, label)

    def setK_i(self, var, label):
        self.canSend.controller_setK_i(self.id, var, label)

    def setK_d(self, var, label):
        self.canSend.controller_setK_d(self.id, var, label)

    def setControllerThreshold(self, var, label):
        self.canSend.controller_setControllerThreshold(self.id, var, label)

    def setVentFailsafePressure(self, var, label):
        self.canSend.controller_setVentFailsafePressure(self.id, var, label)

    def setValveMinimumEnergizeTime(self, var, label):
        self.canSend.controller_setValveMinimumEnergizeTime(self.id, var, label)

    def setValveMinimumDeenergizeTime(self, var, label):
        self.canSend.controller_setValveMinimumDeenergizeTime(self.id, var, label)

    def setCountdownStart(self, var, label):
        self.canSend.controller_setCountdownStart(self.id, var, label)

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

"""
Starts Code
"""

# # This code is initializing the bus variable with the channel and bustype.
# # noinspection PyTypeChecker

CanStatus = False
try:
    import can  # /////////////////////////////////////////////////////////////////////////
    #from CanReceive import CanSend, CanReceive
    from canio_HRC import CanSend, CanReceive
    CanStatus = True

except AttributeError:
    CanStatus = False
except ModuleNotFoundError:
    pass

if CanStatus:

    #busargs = dict(channel='virtual', bustype='virtual')
    busargs = dict(channel='can0', bustype='socketcan')
    
    canReceive = CanReceive(**busargs)
    canSend = CanSend(**busargs)

GUI = Main(canReceive, canSend)
# GUI.run()
GUIThread = Thread(target=GUI.run)
GUIThread.daemon = True

#
GUIThread.start()
if CanStatus:
    canReceive_thread = Thread(target=canReceive.run)
    canReceive_thread.daemon = True
    canReceive_thread.start()
