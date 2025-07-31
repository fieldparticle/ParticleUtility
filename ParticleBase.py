from LogUtility import *
from ConfigUtility import *
import inspect


class ParticleBase:

    widget = None
    """
    This class is the global class for all other classes

    Attributes:
        log (FPIBGLog): FPIBGLog for loogin information and errors
    """
    
    def __init__ (self,ObjName):
        """
        Initializes the object with the application name.

        Args:
            Moniker (string): THe Name of the object.

        
        """
       # print(f"Created " + ObjName)
        self.ObjName = ObjName
        
    def Create(self,CfgFileName,LogName):
        """
        Creates the base object and member objects log and config

        Args:
            self : this.
       
        """

        
        
        self.log = LogUtility("GlobalLoggingObject")   
        self.log.Create(LogName)
        self.log.Open()
        self.cfg = ConfigUtility("GlobalConfigObject")
        self.cfg.Create(self.log,CfgFileName)
        
        #Added by Ben
        self.cfgname = CfgFileName
        
    
    #Added by Ben
    def WriteConfig(self, dict):
        self.cfg.WriteConfig(dict)
        return
       
        
    def connect_to_output(self,widget):
        try:
            self.log.set_out_widget(widget)    
            self.log.log(self,"Linked ot output")
        except BaseException as e:
            self.log.log(self,e)

    def Open(self):
        self.log.Open()
    def Close(self):
        self.log.Close()

    