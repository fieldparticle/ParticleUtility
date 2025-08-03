from gPCDData import *
from AttrDictFields import *

class DataContainer():

    raw_fields_list = []
    fields_list = []
    #******************************************************************
    # init
    #
    def __init__(self, FPIBGBase, itemcfg):
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg
        self.log = self.bobj.log
        self.data_base = None
        self.itemcfg = itemcfg
    
    #******************************************************************
    # Save the DataFields<data_num> configuraton item in a list
    #
    def get_particle_data_fields(self):
        
        more_fields = True
        counter = 1
        self.raw_fields_list.clear()
        while more_fields == True:
            cfg_DataFields = f"DataFields{counter}"
            if cfg_DataFields in self.itemcfg:
                self.raw_fields_list.append(self.itemcfg[cfg_DataFields])
                counter += 1
            else:
                break
        self.parse_fields_list()
        self.resolve_data_files()
        return
    
    #******************************************************************
    # parse the fields from the list and add to a dictionary 
    #
    def parse_fields_list(self):
        count = 0
        for data_lines in self.raw_fields_list:
            for field in data_lines:
                sep_semi_colon = field.split(':')
                sep_period = sep_semi_colon[0].split('.')
            fields_dict = AttrDictFields()
            fields_dict["field"] = sep_semi_colon[1]
            fields_dict["data_base"] = sep_period[1]
            fields_dict["test_type"] = self.itemcfg.mode
            self.fields_list.append(fields_dict)

        return
    #******************************************************************
    # Get the field list
    #
    def get_feilds_list(self):
        return self.fields_list
    
    #******************************************************************
    # Call the first data base and verify
    #
    def do_verify(self):
        field_dict= self.fields_list[0]
        data_obj = field_dict.data_object
        return data_obj.do_verify(field_dict)

    #******************************************************************
    # Return data of summary files
    #   
    def get_data(self):
        for ii in self.fields_list:
            data_obj = ii.data_object
            data_obj.check_data_files(ii)
            data_obj.create_summary(ii)

    #******************************************************************
    # load the data into the fields
    #
    def resolve_data_files(self):
        matches = ["pqb","pcd","cfb","dup","pqbrandom"]    
        for ii in self.fields_list:
            test_fld = ii["data_base"].upper()
            ii["source_dir"] = self.itemcfg.data_dir
            ii["data_object"] = gPCDData(self,self.itemcfg)
            ii["mode"] = self.itemcfg.mode
        return 


        
