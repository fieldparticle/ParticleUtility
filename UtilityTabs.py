import sys
from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton
from PyQt6.QtCore import Qt
from TabFormReport import *
from TabFormGenData import *
## Add all tabs
class UtilityTabs(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    

    ## Add all tabs to this tab form (parent)
    def Create(self,FPIBGBase):
        self.bobj = FPIBGBase
        ## Create the tabs
        self.tabFormGenData = TabGenData()        
        self.tabFormLatex = TabFormReport()
        self.addTab(self.tabFormLatex, 'Reports')
        self.addTab(self.tabFormGenData, 'Generate Data')
        self.tabFormLatex.Create(self.bobj)
        self.tabFormGenData.Create(self.bobj)
      