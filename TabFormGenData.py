import sys
import importlib
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox,QLabel
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6 import QtCore
from PyQt6.QtCore import Qt,QThread,QTimer, pyqtSignal,pyqtSlot,QObject,QRunnable,QThreadPool
from ConfigUtility import *
import tkinter as tk
from tkinter import * 
from tkinter import messagebox 
import glob
import traceback
import time
from PlotParticles import *
import struct
import ctypes
from GenPQBData import *

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
    particle_data = None
    
    #******************************************************************
    # Init
    #
    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        self.threadpool = QThreadPool()
        thread_count = self.threadpool.maxThreadCount()
        #print(f"Multithreading with maximum {thread_count} threads")
        

    def no_selection(self):
        msgBox = QMessageBox()
        msgBox.setText("You have not selected a data file in the list box.")
        msgBox.exec()
    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()
        
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
                return 

            self.plot_obj.create(self.itemcfg,self)
            # update the list
            self.update_list_widget()
            # Enable to generate data
            self.GenDataButton.setEnabled(True)

    #******************************************************************
    # reload the configuration file
    #
    def refresh(self):
        self.load_item_cfg(self.CfgFile)
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
        #module = importlib.import_module(module_name)
        #return getattr(module, class_name)
        return GenPQBData

   
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
        self.do_all_files_dbg()
        #self.start_thread()

    #******************************************************************
    # Update the list widget
    #
    def update_list_widget(self):
        self.ListObj.clear()
        files_names = self.itemcfg.data_dir + "/*.bin"
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
   
    # Thread that does one file set
    #
    def do_one_file(self,progress_callback):
        
        index = self.current_test_file
        try:
            self.gen_class.gen_data_base(index,progress_callback)
        except BaseException as e3:
            print("Thread Error")
            raise BaseException(f"Error writing test file err:{e3}")
            
        return ""

    #******************************************************************
    # Thread that does one file set
    #
    #     
    #******************************************************************
    def do_all_files_dbg(self):
        index = 0
        try:
            for ii in range(len(self.gen_class.select_list)):
                print(f"{ii}")
                self.gen_class.gen_data_base(ii)

        except BaseException as e:
            print(f"do_all_files_dbg err:{e}")
            return
        self.update_list_widget()

    #******************************************************************
    # Thread is complete start a new thread for the next file if there is any
    #
    def thread_complete(self):
        self.current_test_file+=1
        if (self.current_test_file >= len(self.gen_class.select_list)) :
            print(f"Data Set Complete")
            self.update_list_widget()
            return
          # Pass the function to execute
        print(f"Next Thread index:{self.current_test_file}")
        self.start_thread()

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
        if self.itemcfg.test_files_only == False:
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
    # Testing
    # 
    ##############################################################################
    def test_index_array(self):
        selected_item = self.ListObj.selectedItems()
        self.selected_item = selected_item
        if self.selected_item:
           print(selected_item[0].text())
           self.test_array_to_index(selected_item[0].text())
        else:
            self.no_selection()

    def test_array_to_index(self,test_file_name):
        try :
            file_name = f"{self.itemcfg.data_dir}/{self.itemcfg.test_indexing_log}"
            col_file = open(file_name,'w')
            tst_prefix = os.path.splitext(test_file_name)[0]
            tst_file = tst_prefix + '.tst'
            tst_file_obj = ConfigUtility(tst_file)
            tst_file_obj.Create(self.bobj.log,tst_file)
            tst_file_cfg = tst_file_obj.config
            tst_side_length =  tst_file_cfg.CellAryW
            col_file.write(f"Height:{ tst_side_length},Width{tst_side_length}\n")
            col_ary_size = tst_file_cfg.cell_occupancy_list_size
            pu = ParticleUtilities(tst_side_length,col_ary_size)
        except BaseException as e:
            print(f"Verify indexing error:{e}")
            return
        for zz in range(tst_side_length):
            for yy in range(tst_side_length):
                for xx in range(tst_side_length):
                    ary = [round(xx),round(yy),round(zz)]
                    index = pu.ArrayToIndex(ary)
                    col_file.write(f"Index:{index} at <{xx},{yy},{zz}>\n")

        col_file.close()
    """
    #******************************************************************
    # Read the test file and list the index addressing
    # Needs to be consequtive not ,issing numbers
    def verify_particle_count(self,file_name):
        counter = 0
        with open(file_name, "rb") as f:
            while True:
                record = pdata()
                ret = f.readinto(record)
                if ret == 0:
                    break
                counter += 1
            
        print(f"Verify counted :{counter} against {self.number_particles}")
    """ 

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
             self.plot_obj.plot(self.particle_data)
        else:
            self.selected_item = selected_item
            self.plot_obj.close_plot()
        if self.selected_item:
            try:
                self.particle_data = self.read_particle_data(self.selected_item[0].text())
            except BaseException as e:
                self.log.log(self,f"Could not read particle data:{e}")
                return
            try:
                self.plot_obj.plot(self.itemcfg,self.particle_data,self.selected_item[0].text())
            except BaseException as e1:
                self.log.log(self,f"Ploting error:{e1}")
        else:
            self.no_selection()

    #******************************************************************
    # Have plot obj toggle cells
    #
    def toggle_cells(self):
        self.plot_obj.toggle_cells()
    #******************************************************************
    # Have plot obj toggle cell faces
    #    
    def toggle_cell_faces(self):
        self.plot_obj.toggle_cell_face()
    ##############################################################################
    # Setup stuff 
    # 
    ##############################################################################
    
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
        self.log.log(self,"TabFormGenData finished init.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)

            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Generate/Test Particle Data")
            self.setSize(LatexcfgFile,600,600)
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

            self.RefreshButton = QPushButton("Reload")
            self.setSize(self.RefreshButton,30,100)
            self.RefreshButton.setStyleSheet("background-color:  #dddddd")
            self.RefreshButton.clicked.connect(self.refresh)
            dirgrid.addWidget(self.RefreshButton,2,1)

            self.newButton = QPushButton("Plot")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
            self.newButton.clicked.connect(self.plot_particles)
            dirgrid.addWidget(self.newButton,2,2)

            self.GenDataButton = QPushButton("GenData")
            self.setSize(self.GenDataButton,30,100)
            self.GenDataButton.setStyleSheet("background-color:  #dddddd")
            self.GenDataButton.clicked.connect(self.gen_data)
            self.GenDataButton.setEnabled(False)
            dirgrid.addWidget(self.GenDataButton,2,3)

            self.StopButton = QPushButton("Stop Gen")
            self.setSize(self.StopButton,30,100)
            self.StopButton.setStyleSheet("background-color:  #dddddd")
            self.StopButton.clicked.connect(self.gen_data)
            self.StopButton.setEnabled(False)
            dirgrid.addWidget(self.StopButton,2,4)

            self.ToggleCellsBtn = QPushButton("Toggle Cells")
            self.setSize(self.ToggleCellsBtn,30,100)
            self.ToggleCellsBtn.setStyleSheet("background-color:  #dddddd")
            self.ToggleCellsBtn.clicked.connect(self.toggle_cells)
            dirgrid.addWidget(self.ToggleCellsBtn,3,0)

            self.ToggleCellFacesBtn = QPushButton("Toggle Cell Faces")
            self.setSize(self.ToggleCellFacesBtn,30,110)
            self.ToggleCellFacesBtn.setStyleSheet("background-color:  #dddddd")
            self.ToggleCellFacesBtn.clicked.connect(self.toggle_cell_faces)
            dirgrid.addWidget(self.ToggleCellFacesBtn,3,1)

            self.TestArrayBtn = QPushButton("Test Array Indexing")
            self.setSize(self.TestArrayBtn,30,120)
            self.TestArrayBtn.setStyleSheet("background-color:  #dddddd")
            self.TestArrayBtn.clicked.connect(self.test_index_array)
            dirgrid.addWidget(self.TestArrayBtn,3,2)

            self.VerfPCountBtn = QPushButton("Test Particle Count")
            self.setSize(self.VerfPCountBtn,30,120)
            self.VerfPCountBtn.setStyleSheet("background-color:  #dddddd")
            #self.VerfPCountBtn.clicked.connect(self.toggle_cell_faces)
            dirgrid.addWidget(self.VerfPCountBtn,3,3)

            list_label = QLabel("Data Set")
            dirgrid.addWidget(list_label,4,0,1,2)

            self.ListObj =  QListWidget()
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.ListObj,350,450)
            dirgrid.addWidget(self.ListObj,5,0,1,2)

            view_label = QLabel("Views")
            dirgrid.addWidget(view_label,6,0,1,2)

            self.ViewList =  QListWidget()
            self.ViewList.setStyleSheet("background-color:  #FFFFFF")
            self.setSize(self.ViewList,120,450)
            dirgrid.addWidget(self.ViewList,7,0,1,2)
            
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
        self.plot_obj = PlotParticles()

        for ii in self.plot_obj.views:
            self.ViewList.addItem(str(ii))
        self.log.log(self,"TabFormLatex finished Create.")        
        self.load_item_cfg("C:/_DJ/gPCDUtil/ParticleUtility/cfg_gendata/GenPQBSequential.cfg")
   
    def valueChange(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            pass
            #print("List object Value Changed",selected_items[0].text())
           
    