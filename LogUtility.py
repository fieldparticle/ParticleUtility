from datetime import datetime
import inspect
import os

## FPIBGLog class perfomrs formmated logging for all other classes
class LogUtility:
        
    
    ##  FPIBGLog Constructor.
    # @param   ApplicationName --  (string) Passes the name of the calling application.
    def __init__ (self,ApplicationName):
        self.appName = ApplicationName
        #print(type(self))
        

    def CheckLogFile(self,ErrString)-> bool:
        self.Close()
        ret = 0;
        self.FileObj = open(self.logName, "r")
        for line in self.FileObj:
            if ErrString in line:
                #print(line)
                return True
        return False    
    widget = None
    def set_out_widget(self,widget):
        self.widget = widget

    ## Standard create for the log class object.
    # @param   LogName -- (string) the name of the log file which will be written to.
    def Create(self,LogName):
        self.logName = LogName
        #print("Created Log File for ",self.appName)

    def fileObj(self) : pass

    ## This function opens the log file and writes the title header to the log file.
    # The format is:
    # yy,mm,dd,hr,min,application,class,function,object,line number,error code, and error string.
    # 
    def Open(self):
        self.fileObj = open(self.logName,"w")
        logstring = "{}_{}_{}:{}:{},{},{}\n".format("yy",
                                                                    "mm",
                                                                    "dd",
                                                                    "hr",
                                                                    "min",
                                                                    "errText",
                                                                    "eString")
        """
        logstring = "{},{}_{}_{}:{}:{},{},{},{},{},{},{},{}\n".format("lvl",
                                                                    "yy",
                                                                   "mm",
                                                                   "dd",
                                                                   "hr",
                                                                   "min",
                                                                   "Application Name",
                                                                   "ClassName",
                                                                   "Function Name",
                                                                   "ObjName",
                                                                   "Line Number",
                                                                   "ErrCode",
                                                                   "ErrString")
        """
        self.fileObj.write(str(logstring))  
        self.log(self,f"Opened Log File for {self.logName}")

    """
    def logs(self,classObj,ErrString):
        current_time = datetime.now()       
        timestr = "{}_{}_{}:{}:{}".format( current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute)
        logstring = "{},{}\n".format(classObj.ObjName,ErrString)
        self.fileObj.write(str(logstring))  
        self.fileObj.flush()
    """
    ## Write the log item to the log file.
    # @param Line number from import inspect.currentframe().f_lineno
    # @param ClassName from the "__file__" reserved python keyword.
    # @param Object name from the inspect.currentframe().f_code.co_name
    # @param The function name enterred as a string.
    # @param The Object Name from self.ObjName.
    # @param The error code from list to be determined later. Just pass 0 for success and 1 for failure.
    # @param The error text.
    def log(self,parent,ErrString,LogOnly=False,LineNumber=0,ClassName=None,Function=None,ObjName=None):
        current_time = datetime.now()       
        logstring = "{}_{}_{}:{}:{} {} {}".format(current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute,type(parent),ErrString)
        if LogOnly == False:
            if self.widget != None:
                self.widget.append(logstring)
            print(logstring)
        self.fileObj.write(str(logstring)+"\n")  
        self.fileObj.flush()
        
## Standard close. Closes the log file.
    def Close(self):
        self.fileObj.close()