import sys
import importlib
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6 import QtCore
from PyQt6.QtCore import Qt,QThread,QTimer, pyqtSignal,pyqtSlot,QObject
from ConfigUtility import *
import tkinter as tk
from tkinter import * 
from tkinter import messagebox as mb
import glob

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        

    def run(self):
        self.parent.do_one_file()
        self.progress.emit(1)
        self.finished.emit()

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
   

    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def set_up_threading(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker(self)
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.next_thread)
        self.worker.progress.connect(self.reportProgress)
        # Step 6: Start the thread
        

    def reportProgress(self,prog):
        print(prog)

    def __init__(self, *args, **kwargs ):
        super().__init__(*args, **kwargs )
        
    
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def update_cfg_section(self):
        self.ltxObj.clearConfigGrp()
        self.ltxObj.OpenLatxCFG()
        files_names = self.itemcfg.config.data_dir + "/*.bin"
        files = glob.glob(files_names)
        for ii in files:
            self.ListObj.addItem(ii)
        self.SaveButton.setEnabled(True)
        self.GenDataButton.setEnabled(True)
    
    def SaveConfigurationFile(self):
        self.ltxObj.updateCfgData()
        
        #self.ltxObj.clearConfigGrp()

  
    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        self.startDir = self.cfg.gen_start_dir
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.startDir,
                                       ("Configuration File (*.cfg)"))
        # If a valid configuation file name is returned
        if folder[0]:
            self.CfgFile = folder[0]
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
            
    
                
    # Dynamically load the class
    def load_class(self,class_name):
        module_name, class_name = class_name.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

   
    def plot_closed(self):
       pass

    def update_list_widget(self):
        self.ListObj.clear()
        files_names = self.itemcfg.config.data_dir + "/*.bin"
        files = glob.glob(files_names)
        for ii in files:
                self.ListObj.addItem(ii)

    def gen_data(self):
        index = 0
        self.gen_class.create(self,self.itemcfg) 
        # Create the data directory if it does not exist
        try:
            if not os.path.exists(self.itemcfg.data_dir):
                os.makedirs(self.itemcfg.data_dir)
        except BaseException as e1:
            self.log.log(self,f"Error creating data directory:{self.itemcfg.data_dir}, err: {e1}")
        # Open the selections file
        try :
            self.gen_class.open_selections_file()
        except BaseException as e2:
            self.log.log(self,f"Error opening:{self.itemcfg.selections_file_text}, err: {e2}")
        
        self.clear_files()
        self.set_up_threading()
        self.thread.start()
       
    def do_one_file(self):
        try:
            # Calulate the the test propeties
            index = self.current_test_file
            ii = self.gen_class.select_list[index]
            self.gen_class.calulate_test_properties(index,ii)
            self.gen_class.write_test_file(index,ii)
            self.gen_class.create_bin_file()
            self.gen_class.do_cells()
            self.gen_class.close_bin_file()
        except BaseException as e3:
            self.log.log(self,f"Error writing test file err:{e3}")


    def next_thread(self):
        if self.current_test_file>len(self.gen_class.select_list):
            return
        self.set_up_threading()
        self.thread.start()
        self.current_test_file+=1


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
            self.SaveButton.clicked.connect(self.SaveConfigurationFile)
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
        self.bobj.connect_to_output(self.terminal)
   
    def valueChange(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            pass
            #print("List object Value Changed",selected_items[0].text())
            #self.ltxObj.setTypeText(selected_items[0].text())         
    