import pandas as pd
import os
import csv
import re
import statistics
from AttrDictFields import *
class gPCDData():

    sumFile = ""
    average_list = []
    mode = 0
    mmrr_fps = 0.0
    mmrr_cpums = 0.0
    mmrr_gms = 0.0
    MODE_VERF = 1
    MODE_PERF = 0
    data_files = None    
    lines_return = pd.DataFrame()
    
    def __init__(self, FPIBGBase, itemcfg):
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg
        self.log = self.bobj.log
        self.itemcfg = itemcfg

        
    def isNumber(self,value):
        try:
            float(value)
        except ValueError:
            return False
        try:
            int(value)
        except ValueError:
            return False
        return True
    

    #******************************************************************
    # Create thr mmrr summary file
    #
    def do_mmrr(self):
        fps = cpums = cms = gms = expectedp = loadedp = shaderp_comp = shaderp_grph = expectedc = shaderc = sidelen = count = 0
        mmr_path = f"{self.itemcfg.config.data_dir}/mmrr.csv"
        if(os.path.exists(mmr_path) == False):
            print ("MMRR Directories not available" )
            return False
        try:
            with open(mmr_path, 'r') as filename:
                file = csv.DictReader(filename)
                count = 0
                for col in file:
                    count += 1
                    fps += float(col['fps'])
                    cpums += float(col['cpums'])
                    gms += float(col['gms'])
        except BaseException as e:
            print("LatexDataParticle line 159:",e)
            return
        
        self.mmrr_fps = fps / count
        self.mmrr_cpums = cpums / count
        self.mmrr_gms = gms / count    
       

    # Returns true if number of .tst files equal to number of R or D files
    def check_data_files(self,file_dict) -> bool:
        # Check to see if the data directory exists
        if(os.path.exists(file_dict.source_dir) == False):
            raise ValueError(f"check_data_files() inavid directory {file_dict.source_dir}")
        # Get a list of the *.tst files in the data directory
        tst_files = [i for i in os.listdir(file_dict.source_dir) if i.endswith(".tst")]
        # If its verifcation
        if "V" in file_dict.mode:
            file_dict["summary_file_name"] = file_dict.source_dir + "/" + "perfdataVerificationSummary.csv"
            file_dict["err_file_name"] = file_dict.source_dir + "/" + "perfdataVerificationSummaryErrors.csv"
            self.data_files = [i[:-5] for i in os.listdir(file_dict.source_dir) if i.endswith("D.csv")]
        elif "P" in file_dict.mode:
            file_dict["summary_file_name"] = file_dict.source_dir + "/" + "perfdataPerformanceSummary.csv"
            self.data_files = [i[:-5] for i in os.listdir(file_dict.source_dir) if i.endswith("R.csv")]
      

        self.hasData = len(tst_files) == len(self.data_files)
        if(self.hasData == False):
            raise ValueError(f"Data set mismatch. Number *.tst files:{len(tst_files)}, Number data files:{ len(self.data_files)}")
        
        
    #******************************************************************
    # Create the summary file wqith headers
    #
    def create_summary(self,file_dict):
        data = ['Name', 'fps', 'cpums', 'cms', 'gms', 'expectedp', 'loadedp',
                'shaderp_comp', 'shaderp_grph', 'expectedc', 'shaderc', 'sidelen','mean','stddev']
        try :
            with open(file_dict.summary_file_name, mode= 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)
        except BaseException as e:
            raise BaseException(f"create_summary file failed{e}:")
            
    #******************************************************************
    # Run thoruogh the verification files and check counts
    #
    def do_verify(self,file_dict):
        file_count = 0
        error_count = 0
        average_list = []
        for ii in self.data_files:
            try:
                data_file = file_dict.source_dir + "/" + ii + "D.csv"
                with open(data_file, 'r') as filename:
                    file = csv.DictReader(filename)
                    loaded_err = grphp_err = compp_err = coll_err = expectedp = loadedp = shaderp_comp = shaderp_grph = shaderc = 0
                    line_count = 0
                    for col in file:
                        expectedp = int(col['expectedp'])
                        loadedp = int(col['loadedp'])
                        shaderp_comp = int(col['shaderp_comp'])
                        shaderp_grph= int(col['shaderp_grph'])

                        if loadedp != expectedp:
                            loaded_err = 1
                        if shaderp_comp != expectedp:
                            compp_err = 1
                        if shaderp_grph != expectedp:
                            grphp_err = 1
                        
                        expectedc = int(col['expectedc'])
                        shaderc = int(col['shaderc'])
                        
                        if expectedc != shaderc:
                            coll_err = 1

                if loaded_err or grphp_err or compp_err or coll_err:
                    error_count+=1
                    avg_list = [file_count, line_count, expectedp, loadedp, shaderp_comp,
                        shaderp_grph, expectedc, shaderc, loaded_err, compp_err, grphp_err, coll_err]
                    average_list.append(avg_list)            
                line_count += 1
            except BaseException as e:
                raise BaseException(f"do_verify - summary file open error:{e}")
            file_count += 1

        with open(file_dict.err_file_name, 'w', newline='\n') as file:
            writer = csv.writer(file)
            writer.writerow( ['file_count', 'line_count', 'expectedp', 'loadedp', 'shaderp_comp',
                        'shaderp_grph','expectedc', 'shaderc', 'loaded_err', 'compp_err', 'grphp_err', 'coll_err'])
            if error_count > 0:
                for ii in range(len(average_list)):
                    writer.writerow(average_list[ii])
        return error_count
            
    #******************************************************************
    # Get averages
    #
    def get_averages(self):
        if(self.hasData == False):
            return
        print("Performing Averages")
        self.average_list = []
        for i in self.data_files:
            if self.mode == 0:
                file_path_release = self.topdir + "/" + i + "R.csv"
            else:
                file_path_debug = self.topdir + "/" + i + "D.csv"
            fps = cpums = cms = gms = expectedp = loadedp = shaderp_comp = shaderp_grph = expectedc = shaderc = sidelen = count = 0
        
            try:
                with open(file_path_release, 'r') as filename:
                    file = csv.DictReader(filename)
                    for col in file:
                        
                        count += 1
                        fps += float(col['fps'])
                        cpums += float(col['cpums'])
                        cms += float(col['cms'])
                        gms += float(col['gms'])
                        if count == 1:
                            loadedp = float(col['loadedp'])
                            expectedc = int(col['expectedc'])
                            sidelen = int(col['sidelen'])
                            
            except BaseException as e:
                print("LatexDataParticle get_averages line 282:",e)

            fps = fps / count
            cpums = cpums / count
            cms = cms / count
            gms = gms / count
            shaderp_comp = shaderp_comp / count
            shaderp_grph = shaderp_grph / count
            shaderc = shaderc / count
            avg_list = [i, fps, cpums, cms, gms, expectedp, loadedp, shaderp_comp,
                        shaderp_grph, expectedc, shaderc, sidelen]
            with open(self.sumFile, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(avg_list)
            self.average_list.append(avg_list)
        file.close()
    #******************************************************************
    # Get maximuns write then to summary file
    #
    def get_maxes(self,file_dict):
        if(self.hasData == False):
            return
        print("Performing Maximums")
        for i in self.data_files:
            fps_old = 0
            cpums_old = 0.0
            cms_old = 0.0
            gms_old = 0.0
            if self.mode == 0:
                file_path_release = self.topdir + "/" + i + "R.csv"
            else:
                file_path_release = self.topdir + "/" + i + "D.csv"
            mean = stddev = fps = cpums = cms = gms = expectedp = loadedp = shaderp_comp = shaderp_grph = expectedc = shaderc = sidelen = count = 0
            fps_list = []
          
            try:
                with open(file_path_release, 'r') as filename:
                    file = csv.DictReader(filename)
                    for col in file:
                        
                        count += 1
                        fps = float(col['fps'])
                        fps_list.append(fps)
                        if fps > fps_old:
                            fps_old = fps
                        cpums = float(col['cpums'])
                        if cpums > cpums_old:
                            cpums_old = cpums
                        cms = float(col['cms'])
                        if cms > cms_old:
                            cms_old = cms
                        gms = float(col['gms'])
                        if gms > gms_old:
                            gms_old = gms
                        if count == 1:
                            loadedp = float(col['loadedp'])
                            expectedc = int(col['expectedc'])
                            sidelen = int(col['sidelen'])
            except BaseException as e:
                print("LatexDataParticle get_averages line 282:",e)

            mean = statistics.mean(fps_list)
            stddev = statistics.stdev(fps_list)
           
            max_list = [i, fps_old, cpums_old, cms_old, gms_old, expectedp, loadedp, shaderp_comp,
                        shaderp_grph, expectedc, shaderc, sidelen,mean,stddev]
            with open(file_dict.err_file_name, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(max_list)
            self.average_list.append(max_list)
        file.close()