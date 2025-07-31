import sys
import importlib
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6 import QtCore
from PyQt6.QtCore import Qt,QThread,QTimer, pyqtSignal,pyqtSlot,QObject,QRunnable,QThreadPool
from ConfigUtility import *
import tkinter as tk
from tkinter import * 
from tkinter import messagebox as mb
import glob
import traceback
import time
from PlotParticles import *
import struct
import ctypes

class pdata(ctypes.Structure):
    _fields_ = [("pnum", ctypes.c_double),
                ("rx",  ctypes.c_double),
                ("ry",  ctypes.c_double),
                ("rz",  ctypes.c_double),
                ("radius",  ctypes.c_double),
                ("vx",  ctypes.c_double),
                ("vy",  ctypes.c_double),
                ("vz",  ctypes.c_double),
                ("ptype",  ctypes.c_double),
                ("seq",  ctypes.c_double),
                ("acc_r",  ctypes.c_double),
                ("Acc_a",  ctypes.c_double),
                ("molar_mass",  ctypes.c_double),
                ("temp_vel",  ctypes.c_double)]          

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(float)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        # Add the callback to our kwargs
        self.kwargs["progress_callback"] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class TabGenData(QTabWidget):
    
    texFolder = ""
    CfgFile = ""
    texFileName = ""
    hasConfig = False
    itemcfg = None
    selected_item = -1
    #ObjName = ""
    gen_class = None
    thread = None
    current_test_file = 0
    
        
    ##############################################################################
    # Configuration file stuff
    # 
    ##############################################################################

    #******************************************************************
    # Load the configuration data
    #
    def load_item_cfg(self,file):
            self.CfgFile = file
            self.texFolder = os.path.dirname(self.CfgFile)
            self.texFileName = os.path.splitext(os.path.basename(self.CfgFile))[0]
            self.dirEdit.setText(self.CfgFile)

            # Open the item configuration filke
            try :
                self.itemcfgFile = ConfigUtility(self.CfgFile)
                self.itemcfgFile.Create(self.bobj.log,self.CfgFile)
                self.itemcfg = self.itemcfgFile.config
                
            except BaseException as e:
                self.log.log(self,f"Unable to open item configurations file:{e}")
                self.hasConfig = False
                return 
            try:
                # Import the class named in generate_class
                self.gen_class = self.load_class(self.itemcfg.generate_class)()    
            except BaseException as e:
                self.log.log(self,f"Unable to import data generation file: {self.itemcfg.generate_class} error:{e}")

            # Enable to generate data
            self.GenDataButton.setEnabled(True)
    
    #******************************************************************
    # Browse to an existing cfg file
    #
    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        self.startDir = self.cfg.gen_start_dir
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.startDir,
                                       ("Configuration File (*.cfg)"))
        # If a valid configuation file name is returned
        if folder[0]:
            self.load_item_cfg(folder[0])
    #******************************************************************
    # Dynamically load the class
    #           
    def load_class(self,class_name):
        module_name, class_name = class_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

   
    ##############################################################################
    # Generate data stuff
    # 
    ##############################################################################
    #******************************************************************
    # Start the data threaded generaton process
    #
    def gen_data(self):
         # Pass the function to execute
        index = 0
        self.current_test_file = 0
        self.gen_class.create(self,self.itemcfg) 
        # Create the data directory if it does not exist
        try:
            if not os.path.exists(self.itemcfg.data_dir):
                os.makedirs(self.itemcfg.data_dir)
        except BaseException as e1:
            self.log.log(self,f"Error creating data directory:{self.itemcfg.data_dir}, err: {e1}")
        # Open the selections file
        self.gen_class.clear_selections()
        try :
            self.gen_class.open_selections_file()
        except BaseException as e2:
            self.log.log(self,f"Error opening:{self.itemcfg.selections_file_text}, err: {e2}")
        
        self.clear_files()
        self.start_thread()

    #******************************************************************
    # Update the list widget
    #
    def update_list_widget(self):
        self.ListObj.clear()
        files_names = self.itemcfg.config.data_dir + "/*.bin"
        files = glob.glob(files_names)
        for ii in files:
                self.ListObj.addItem(ii)

    def print_output(self, s):
        print(s)
    #******************************************************************
    # Set up and start the thread
    #
    def start_thread(self):
        try :
            self.terminal.clear()
            worker = Worker(self.do_one_file )  # Any other args, kwargs are passed to the run function
            worker.signals.result.connect(self.print_output)
            worker.signals.finished.connect(self.thread_complete)
            worker.signals.progress.connect(self.update_terminal)
            # Execute
            self.threadpool.start(worker)
        except BaseException as e:
            print(f"Start Thread Failed:{e}")
   
    #******************************************************************
    # Thread is complete start a new thread for the next file if there is any
    #
    def thread_complete(self):
        self.current_test_file+=1
        if (self.current_test_file >= len(self.gen_class.select_list)) :
            print(f"COMPLETE!")
            return
          # Pass the function to execute
        print(f"Next Thread index:{self.current_test_file}")
        self.start_thread()
        
    #******************************************************************
    # Thread that does one file set
    #
    def do_one_file(self,progress_callback):
        
        try:
            # Calulate the the test propeties
            index = self.current_test_file
            ii = self.gen_class.select_list[index]
            print(f"{index}:{ii}")
            self.gen_class.calulate_test_properties(index,ii)
            self.gen_class.write_test_file(index,ii)
            self.gen_class.create_bin_file()
            self.gen_class.do_cells(progress_callback)
            self.gen_class.close_bin_file()
        except BaseException as e3:
            print("Thread Error")
            raise BaseException(f"Error writing test file err:{e3}")
            
        return ""

    #******************************************************************
    # Update the terminal window
    #
    def update_terminal(self,n):
        print(f"{n:.3f}% done")
        self.terminal.append(f"{n:.3f}% done")

    #******************************************************************
    # Clear the files in the data directory
    #
    def clear_files(self):
        clr_path = self.itemcfg.data_dir + "/*.csv"
        files = glob.glob(clr_path)
        for f in files:
            os.remove(f)

        clr_path = self.itemcfg.data_dir + "/*.bin"
        files = glob.glob(clr_path)
        for f in files:
            os.remove(f)
        
        clr_path = self.itemcfg.data_dir + "/*.tst"
        files = glob.glob(clr_path)
        for f in files:
            os.remove(f)
    #******************************************************************
    # Read the data from a file and return os as 
    #
    def read_particle_data(self,file_name):
        if(self.ListObj.currentRow() < 0):
            mb.messagebox('No data file has been selected')
            

            
        struct_fmt = 'dddddddddddddd'
        struct_len = struct.calcsize(struct_fmt)
        #print(struct_len)
        struct_unpack = struct.Struct(struct_fmt).unpack_from
        count = 0
        results = []
        
        with open(file_name, "rb") as f:
            
            while True:
                record = pdata()
                ret = f.readinto(record)
                if ret == 0:
                    break
                results.append(record)
        p_lst = []
        return results
    

    ##############################################################################
    # Plot stuff
    # 
    ##############################################################################
    #******************************************************************
    # Thread is complete start a new thread for the next file if there is any
    #
    def plot_particles(self):
        
        selected_item = self.ListObj.selectedItems()
        if selected_item ==self.selected_item:
            return
        else:
            self.selected_item = selected_item
            #self.ltxObj.close_plot()
        #if self.selected_item:
           
            #self.ltxObj.plot(self.selected_item[0].text())
        #else:
         #   print("No Database item is selected.")
       
    ##############################################################################
    # Setup stuff 
    # 
    ##############################################################################
    #******************************************************************
    # Init
    #
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        self.threadpool = QThreadPool()
        thread_count = self.threadpool.maxThreadCount()
        #print(f"Multithreading with maximum {thread_count} threads")
        
    #******************************************************************
    # Set the size of a widget
    #
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)
    #******************************************************************
    # Creatwe the tab
    #
    def Create(self,ParticleBase):
        self.bobj = ParticleBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)

            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Generate/Test Particle Data")
            self.setSize(LatexcfgFile,450,600)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            self.dirEdit =  QLineEdit()
            self.dirEdit.setStyleSheet("background-color:  #ffffff")
            self.dirEdit.setText("")
            self.setSize(self.dirEdit,30,450)

            self.dirButton = QPushButton("Browse")
            self.setSize(self.dirButton,30,100)
            self.dirButton.setStyleSheet("background-color:  #dddddd")
            self.dirButton.clicked.connect(self.browseFolder)
            dirgrid.addWidget(self.dirButton,0,0)
            dirgrid.addWidget(self.dirEdit,0,1)

            self.SaveButton = QPushButton("Save")
            self.setSize(self.SaveButton,30,100)
            self.SaveButton.setStyleSheet("background-color:  #dddddd")
            #self.SaveButton.clicked.connect(self.SaveConfigurationFile)
            self.SaveButton.setEnabled(False)
            dirgrid.addWidget(self.SaveButton,2,0)

            self.newButton = QPushButton("Plot")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
            self.newButton.clicked.connect(self.plot_particles)
            dirgrid.addWidget(self.newButton,2,1)

            self.GenDataButton = QPushButton("GenData")
            self.setSize(self.GenDataButton,30,100)
            self.GenDataButton.setStyleSheet("background-color:  #dddddd")
            self.GenDataButton.clicked.connect(self.gen_data)
            self.GenDataButton.setEnabled(False)
            dirgrid.addWidget(self.GenDataButton,2,2)

            self.StopButton = QPushButton("Stop Gen")
            self.setSize(self.StopButton,30,100)
            self.StopButton.setStyleSheet("background-color:  #dddddd")
            self.StopButton.clicked.connect(self.gen_data)
            self.StopButton.setEnabled(False)
            dirgrid.addWidget(self.StopButton,2,3)

            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.ListObj,350,450)
            self.vcnt = 0            
            #self.ListObj.itemSelectionChanged.connect(lambda: self.valueChangeArray(self.ListObj))
            dirgrid.addWidget(self.ListObj,3,0,1,2)
            self.log.log(self,"TabFormLatex finished Create.")
            

            
            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.tab_layout.addWidget(self.terminal,5,0,3,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,f"Error in Create:{e}")
            return 
        self.bobj.connect_to_output(self.terminal)

        self.load_item_cfg("C:/_DJ/gPCDUtil/ParticleUtility/cfg_gendata/GenPQBSequential.cfg")
   
    def valueChange(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            pass
            #print("List object Value Changed",selected_items[0].text())
            #self.ltxObj.setTypeText(selected_items[0].text())         
    