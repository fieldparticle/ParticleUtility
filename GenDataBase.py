import struct
import os
import csv
#from mpl_interactions import ioff, panhandler, zoom_factory
#import plotly.express as px
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import ctypes
import math
from ConfigUtility import *
from abc import ABC, abstractmethod


	#double rx;
	#double ry;
	#double rz;
	#double radius;
	#double vx;
	#double vy;
	#double vz;
	#double ptype;
	#double seq;
	#double acc_r;
	#double acc_a;
	#double molar_mass;
	#double temp_vel;
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
          


class GenDataBase:

    #tst_file_cfg = ConfigUtility("tstFIleCfg")
    particle_list = []
    particle_count = 0
    collision_count = 0
    collsions_in_cell_count = 0
    particles_in_cell_count = 0
    select_list = []
    sepdist = 0.05
    bin_file = None
    particle_separation = 0.0
    
    views = [('XY',   (90, -90, 0)),
        ('XZ',    (0, -90, 0)),
        ('YZ',    (0,   0, 0)),
        ('-XY', (-90,  90, 0)),
        ('-XZ',   (0,  90, 0)),
        ('-YZ',   (0, 180, 0))]   
    
    def __init__(self):
       pass

    def create(self,parent,itemcfg):
        self.parent = parent
        self.bobj = parent.bobj
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.itemcfg = itemcfg
    
    # Impliment in subclass
    def place_particles(self,xx,yy,zz,row,col,layer,w_list):
        pass

    # Impliment in subclass
    def do_cells(self):
        pass

    def on_close(self,event):
        pass

    def create_bin_file(self):
        try:
            self.bin_file = open(self.test_bin_name,"wb")
        except BaseException as e:
            self.log.log(self,e)
        self.count = 0

    
    def write_bin_file(self,w_lst):
        try:
            for ii in w_lst:
                self.bin_file.write(ii)
                self.count+=1
        except BaseException as e:
            self.log.log(self,e)
        
    def close_bin_file(self):
        self.bin_file.flush()
        self.bin_file.close()
        if(self.bin_file.closed != True):
            self.bobj.log.log("File:{self.test_bin_name} not closed")
        
    def write_test_file(self):
        if not os.path.exists(os.path.isdir(self.itemcfg.data_dir)):
            os.makedirs(os.path.isdir(self.itemcfg.data_dir))

    def gen_data_base(self):
        if not os.path.exists(self.itemcfg.data_dir):
            os.makedirs(self.itemcfg.data_dir)
        # Scan each line of the selections list, calulate properties, and gen data
        self.open_selections_file()
        index = 0
        
        for ii in self.select_list:
            self.calulate_cell_properties(index,ii)
            self.write_test_file(index,ii)
            self.open_bin_file()
            self.do_cells()
            self.close_bin_file()
            self.bobj.log.log(self,f"Wrote {self.count} particle to {self.test_bin_name}")
            index+=1
        self.select_list.clear()

        # Define the event handling function
    def calc_test_parms(self):
        pass

    # load all lines from the particle selections file into selections list
    def open_selections_file(self):
        with open(self.itemcfg.selections_file,"r",newline='') as csvfl:
            reader = csv.DictReader(csvfl, delimiter=',',dialect='excel')
            for row in reader:
                if row["sel"] == 's':
                    self.select_list.append(row)
    
    def clear_selections(self):
        self.select_list.clear()
       
    def calulate_test_properties(self,index,sel_dict):
        try :
            self.collision_density      = float(sel_dict['cdens'])
            self.number_particles       =  int(sel_dict['tot'])
            self.radius                 = float(sel_dict['radius'])
            self.sepdist                =  self.itemcfg.particle_separation
        except BaseException as e:
            raise ValueError(f"Key error in record at calulate_cell_properties:{e}")
        
        
        self.center_line_length          = 2*self.radius  + self.radius*self.sepdist
        self.particles_in_row       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_col       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_layers    = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_cell      = self.particles_in_row*self.particles_in_col*self.particles_in_layers
        #self.particles_in_space	    = int(self.particles_in_row*self.particles_in_col*self.particles_in_layers)
        # Somtimes we do very small number of particles to check the pattern
        self.cell_array_size      = self.particles_in_cell+10
        self.num_collisions_per_cell = math.ceil(self.particles_in_cell * self.collision_density/2.0)
        # Calulate side length based on particles per cell
        side_len = 0
        
        while side_len < 1000:
            side_len += 1
            if (side_len * side_len * side_len * self.particles_in_cell >= self.number_particles):
                break
        print(f"Break at {side_len}")
        
        self.side_length = side_len
        self.cell_x_len = self.side_length+1
        self.cell_y_len = self.side_length+1
        self.cell_z_len = self.side_length+1
        
        self.tot_num_cells = self.number_particles / self.particles_in_cell
        self.tot_num_collsions = math.ceil(int(self.tot_num_cells *self.num_collisions_per_cell*2.0 ))
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(index,self.number_particles,self.tot_num_collsions,side_len)
        self.test_file_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.itemcfg.data_dir + '/' + self.set_file_name
        return 
        # This crashes 
        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}, Separation Dist: {self.sepdist }, Center line length: {self.center_line_length:.2f}",LogOnly=True)
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}",LogOnly=True)
        self.log.log(self,f"Particles in space: {self.particles_in_space}, Cell array size: {self.cell_array_size }",LogOnly=True)

    def write_test_file(self,index,sel_dict):

        try:
            f = open(self.test_file_name,'w')
        except BaseException as e:
            raise BaseException(f"Can't open testfile {self.test_file_name} err{e}")
        fstr = f"index = {index}\n"     
        f.write(fstr)
        fstr = f"CellAryW = {self.cell_x_len+1};\n"     
        f.write(fstr)
        fstr = f"CellAryH = {self.cell_y_len+1};\n"     
        f.write(fstr)
        fstr = f"CellAryL = {self.cell_z_len+1};\n"     
        f.write(fstr)
      
        fstr = f"radius = {float(self.radius)};\n"
        f.write(fstr)
        fstr = f"PartPerCell = {self.particles_in_cell};\n"
        f.write(fstr)
        fstr = f"pcount = {self.number_particles};\n"
        f.write(fstr)
        fstr = f"colcount = {self.tot_num_collsions};\n"
        f.write(fstr)
        fstr = f"dataFile = \"{self.test_bin_name};\"\n"
        f.write(fstr)
        fstr = f"aprFile = \"{ self.report_file};\"\n"
        f.write(fstr)
        fstr = f"density = {sel_dict['cdens']};\n"
        f.write(fstr)
        fstr = f"pdensity = 0;\n"
        f.write(fstr)
        fstr = f"dispatchx = {sel_dict['wx']};\n"
        f.write(fstr)
        fstr = f"dispatchx = {sel_dict['wy']};\n"
        f.write(fstr)
        fstr = f"dispatchx = {sel_dict['wz']};\n"
        f.write(fstr)
        fstr = f"dispatchx = {sel_dict['dx']};\n"
        f.write(fstr)
        fstr = f"dispatchx = {sel_dict['dx']};\n"
        f.write(fstr)
        fstr = f"dispatchx = {sel_dict['dz']};\n"
        f.write(fstr)
        fstr = f"ColArySize = {self.cell_array_size};\n"
        f.write(fstr)
        f.flush()
        f.close()


  
