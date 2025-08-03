import sys
from contextlib import redirect_stdout
from io import StringIO
from sys import stderr, stdout
from PyQt6.QtCore import Qt,QObject
from PyQt6.QtWidgets import QFileDialog, QGroupBox,QMessageBox
from PyQt6.QtWidgets import QGridLayout, QTabWidget, QLineEdit,QListWidget
from PyQt6.QtWidgets import QPushButton, QGroupBox,QTextEdit
from PyQt6 import QtCore
from _thread import *
from ConfigUtility import *
from DataContainer import *
class TabFormReport(QTabWidget):
    
    texFolder = ""
    CfgFile = ""
    texFileName = ""
    hasConfig = False
    itemcfg = ConfigUtility("Latex Class")
    startDir = "J:/MOD/FPIBGUtility/Latex"
    startDir = "J:/FPIBGJournalStaticV2/rpt"
    startDir = "J:/FPIBGJournalStaticV2/cfg"
    data_container = None
    latex_container = None
    interpeter = None

    ObjName = ""
    ltxObj = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        
    
    def setSize(self,control,H,W):
        control.setMinimumHeight(H)
        control.setMinimumWidth(W)
        control.setMaximumHeight(H)
        control.setMaximumWidth(W)

    def SaveConfigurationFile(self):
        self.ltxObj.updateCfgData()
        
        #self.ltxObj.clearConfigGrp()

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
                self.log.log(self,f"Config File syntax - line number of config file:{e}")
                self.hasConfig = False
                return 
            
            self.data_container = DataContainer(self,self.itemcfg)
            self.data_container.get_particle_data_fields()
            self.VerifyButton.setEnabled(True)

    def browseFolder(self):
        """ Opens a dialog window for the user to select a folder in the file system. """
        #folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        folder = QFileDialog.getOpenFileName(self, ("Open File"),
                                       self.startDir,
                                       ("Configuration File (*.cfg)"))
        
        if folder[0]:
           self.load_item_cfg(folder[0])


    def msg_box(self,text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.exec()

    def preview(self):
        pass    

    def verify(self):
        try :
            self.data_container.get_data()
            ret = self.data_container.do_verify()
            if ret > 0:
                field_dict = self.data_container.get_feilds_dict()
                self.msg_box(f"Verify failed: Number of errors:{ret}. See ")
            else:
                self.msg_box(f"Verify Passed!")
        except BaseException as e:
            print(f"Verify Failed:{e}")

        pass

    def Create(self,FPIBGBase):
        
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        self.log.log(self,"TabFormLatex started Create.")
        try:
            self.setStyleSheet("background-color:  #eeeeee")
            self.tab_layout = QGridLayout()
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.setLayout(self.tab_layout)

            ## -------------------------------------------------------------
            ## Set parent directory
            LatexcfgFile = QGroupBox("Report Configuraiton")
            self.setSize(LatexcfgFile,600,600)
            self.tab_layout.addWidget(LatexcfgFile,0,0,2,2,alignment= Qt.AlignmentFlag.AlignLeft)
            
            dirgrid = QGridLayout()
            LatexcfgFile.setLayout(dirgrid)

            self.dirEdit =  QLineEdit()
            self.dirEdit.setStyleSheet("background-color:  #ffffff")
            self.dirEdit.setText("")

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

            self.newButton = QPushButton("New")
            self.setSize(self.newButton,30,100)
            self.newButton.setStyleSheet("background-color:  #dddddd")
           # self.newButton.clicked.connect(self.browseNewItem)
            dirgrid.addWidget(self.newButton,2,1)

            self.VerifyButton = QPushButton("Verify")
            self.setSize(self.VerifyButton,30,100)
            self.VerifyButton.setStyleSheet("background-color:  #dddddd")
            self.VerifyButton.clicked.connect(self.verify)
            self.VerifyButton.setEnabled(False)
            dirgrid.addWidget(self.VerifyButton,2,3)


            self.PreviewButton = QPushButton("Preview")
            self.setSize(self.PreviewButton,30,100)
            self.PreviewButton.setStyleSheet("background-color:  #dddddd")
            self.PreviewButton.clicked.connect(self.preview)
            self.PreviewButton.setEnabled(False)
            dirgrid.addWidget(self.PreviewButton,2,2)

            self.ListObj =  QListWidget()
            #self.ListObj.setFont(self.font)
            self.ListObj.setStyleSheet("background-color:  #FFFFFF")
            self.vcnt = 0            
            self.ListObj.insertItem(0, "image")
            self.ListObj.insertItem(1, "plot")
            self.ListObj.insertItem(2, "multiplot")
            self.ListObj.insertItem(3, "multiimage")
            self.ListObj.itemSelectionChanged.connect(lambda: self.valueChangeArray(self.ListObj))
            dirgrid.addWidget(self.ListObj,3,0,1,2)
            

            ## -------------------------------------------------------------
            ## Comunications Interface
            self.terminal =  QTextEdit(self)
            self.terminal.setStyleSheet("background-color:  #ffffff; color: green")
            self.setSize(self.terminal,225,900)
            self.tab_layout.addWidget(self.terminal,4,0,1,3,alignment= Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        except BaseException as e:
            self.log.log(self,e)
        try:
            self.load_item_cfg("C:/_DJ/gPCDUtil/ParticleUtility/cfg_reports/PQBOnly.cfg")
        except BaseException as e1:
            print(f"Cannot open cfg file:{e1}")
   
    def valueChangeArray(self,listObj):  
        selected_items = listObj.selectedItems()
        if selected_items:
            #print("List object Value Changed",selected_items[0].text())
            self.ltxObj.setTypeText(selected_items[0].text())         
    