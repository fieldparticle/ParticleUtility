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

    tst_file_cfg = ConfigUtility("tstFIleCfg")
    particle_list = []
    particle_count = 0
    collision_count = 0
    collsions_in_cell_count = 0
    particles_in_cell_count = 0
    select_list = []
    sepdist = 0.05
    bin_file = None
    start_cell = 0
    end_cell = 0
    flg_plt_exists  = False
    toggle_flag = False
    cur_view_num = 0
    cur_file = ""
    flg_plot_cell_faces = False
    flg_plot_cells = False

    views = [('XY',   (90, -90, 0)),
        ('XZ',    (0, -90, 0)),
        ('YZ',    (0,   0, 0)),
        ('-XY', (-90,  90, 0)),
        ('-XZ',   (0,  90, 0)),
        ('-YZ',   (0, 180, 0))]   
    
    def __init__(self):
       pass

    def Create(self, FPIBGBase, ObjName,itemcfg,parent):
        self.parent = parent
        self.ObjName = ObjName
        self.bobj = FPIBGBase
        self.cfg = self.bobj.cfg.config
        self.log = self.bobj.log
        self.log.log(self,"TabFormLatex finished init.")
        self.itemcfg = itemcfg
        self.cfg = self.itemcfg
        self.cur_view_num = int(self.cfg.default_view_text)
        self.toggle_flag = False
      

    def on_close(self,event):
        pass

        
    @abstractmethod
    def gen_data(self):
        pass
    @abstractmethod
    def plot_particle_cell(self):
        pass

    @abstractmethod
    def place_particles(self,row,column):
        pass
    
    @abstractmethod
    def do_cells(self):
        pass
    
    
    def open_bin_file(self):
        try:
            if self.bin_file:
                del self.bin_file
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
        if not os.path.exists(os.path.isdir(self.cfg.data_dir)):
            os.makedirs(os.path.isdir(self.cfg.data_dir))

    def gen_data_base(self):
        if not os.path.exists(self.cfg.data_dir):
            os.makedirs(self.cfg.data_dir)
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
        try:
            with open(self.cfg.selections_file_text,"r",newline='') as csvfl:
                reader = csv.DictReader(csvfl, delimiter=',',dialect='excel')
                for row in reader:
                    if row["sel"] == 's':
                        self.select_list.append(row)
                        
                        
        except BaseException as e:
            self.log.log(self,f"Error opening:{self.cfg.selections_file_text}, err:", e)

       
    def calulate_cell_properties(self,index,sel_dict):
        try :
            self.collision_density           = float(sel_dict['cdens'])
            self.number_particles       =  int(sel_dict['tot'])
            self.radius                 = float(sel_dict['radius'])
            self.sepdist                =  float(self.cfg.particle_separation_text)
        except BaseException as e:
            self.log.log(self,f"Key error in record:",e)
        self.center_line_length          = 2*self.radius  + self.radius*self.sepdist
        self.particles_in_row       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_col       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_layers    = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_cell      = self.particles_in_row*self.particles_in_col*self.particles_in_layers
        self.particles_in_space	    = int(self.particles_in_row*self.particles_in_col*self.particles_in_layers)
        # Somtimes we do very small number of particles to check the pattern
        if (self.particles_in_space > self.number_particles):
            self.particles_in_space = self.number_particles
        self.cell_array_size      = self.particles_in_space+10
        self.num_collisions_per_cell = math.ceil(self.particles_in_space * self.collision_density/2.0)
        # Calulate side length based on particles per cell
        side_len = 0
        while True:
            side_len += 1
            if (side_len * side_len * side_len * self.particles_in_space >= self.number_particles):
                break
        self.side_length = side_len
        self.cell_x_len = self.side_length+1
        self.cell_y_len = self.side_length+1
        self.cell_z_len = self.side_length+1
        self.tot_num_cells = self.number_particles / self.particles_in_space
        self.tot_num_collsions = math.ceil(int(self.tot_num_cells *self.num_collisions_per_cell*2.0 ))
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(index,self.number_particles,self.tot_num_collsions,side_len)
        self.test_file_name = self.cfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.cfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.cfg.data_dir + '/' + self.set_file_name

        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}, Separation Dist: {self.sepdist }, Center line length: {self.center_line_length:.2f}")
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Particles in space: {self.particles_in_space}, Cell array size: {self.cell_array_size }")

    def write_test_file(self,index,sel_dict):
        
        with open(self.test_file_name,'w') as f:
            fstr = f"index = {index}\n"     
            f.write(fstr)
            fstr = f"CellAryW = {self.cell_x_len+1};\n"     
            f.write(fstr)
            fstr = f"CellAryH = {self.cell_y_len+1};\n"     
            f.write(fstr)
            fstr = f"CellAryL = {self.cell_z_len+1};\n"     
            f.write(fstr)
            fstr = f"radius = {self.radius};\n"
            f.write(fstr)
            fstr = f"PartPerCell = {self.particles_in_space};\n"
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
        f.close()


  
    
# Connect the event handler to the source figure
####################################################################################################
    def toggle_cell_face(self):
        if self.flg_plot_cell_faces == True:
            self.flg_plot_cell_faces = False
        else:
            self.flg_plot_cell_faces = True
        if self.flg_plot_cells == True:
            self.update_plot()
        else:
            print("Plotting cells is off.")

    def toggle_cells(self):
        if(self.flg_plot_cells == True):
            self.flg_plot_cells = False
        else:
            self.flg_plot_cells = True
        self.update_plot()

    def set_view_num(self,viewnum):
        self.cur_view_num = viewnum

    def set_cell_toggle_flag(self, flag):
        self.toggle_flag = flag

    def close_plot(self):
        plt.close()

    def set_up_plot(self):
        self.fig = plt.figure(1,figsize=(12, 10))
        self.ax = self.fig.add_subplot(projection='3d')
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        

    def do_plot(self,view_num=None,cells_on=True):
        self.plot_particles(self.plist,aspoints=False)
        if self.flg_plot_cells == True:
            for ii in range(self.tst_side_length):
                for jj in range(self.tst_side_length):
                    for kk in range(self.tst_side_length):
                        self.plot_cells(ii,jj,kk)

        self.end_plot()
        self.flg_plt_exists  = True

    def update_plot(self): 
        plt.cla()
        self.do_plot()
        plt.show(block=False)
        plt.pause(0.01)
        
    def plot_base(self,file_name,view_num=None,cells_on=True):
        self.cur_file = file_name        
        self.set_up_plot()
        file_prefix = os.path.splitext(file_name)[0]
        self.test_file_name = file_prefix + ".tst"
        self.tst_file_cfg.Create(self.bobj.log,self.test_file_name)
        self.tst_side_length = int(self.cfg.start_sidelen_text)
        self.plist = self.read_particle_data(file_name)
        self.do_plot()
        plt.show(block=False)
        
    def side_value_changed(self,side_txt):
        if len(side_txt) < 2:
            return None
        self.start_cell = int(side_txt[0])
        self.end_cell = int(side_txt[1])
        
    def plot_view_changed(self,view):
        self.fig.canvas.draw()

    def end_plot(self,sidelen = None):
        view_num=self.cur_view_num
        self.ax.view_init(elev=self.views[view_num][1][0], azim=self.views[view_num][1][1], roll=self.views[view_num][1][2])
        self.ax.set_title('3D Line Plot')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        if sidelen != None:
            lims = [0,sidelen+1]
            self.ax.set_xlim(lims)
            self.ax.set_ylim(lims)
            self.ax.set_zlim(lims)
        else:
            mxlims =[0,4]
            #ylims = max(npplist[:,2])
            #mzlims = max(npplist[:,3])
            lims = [0,5]
            self.ax.set_xlim(lims)
            self.ax.set_ylim(lims)
            self.ax.set_zlim(lims)
        self.ax.set_title('3D Sphere')
        plt.gca().set_aspect('equal')
        #plt.get_current_fig_manager().full_screen_toggle()
        


    def get_side_length_txt(self):
        side_txt = f"{self.tst_side_length}:{self.tst_side_length}"
        
    def plot_cells(self,cx,cy,cz):
        R = 0.5
        pt_lst = np.zeros((8,3))
        pt_lst[0]= [cx-R,cy-R,cz-R]
        pt_lst[1]= [cx+R,cy-R,cz-R]
        pt_lst[2]= [cx+R,cy+R,cz-R]
        pt_lst[3]= [cx-R,cy+R,cz-R]
        pt_lst[4]= [cx-R,cy-R,cz+R]
        pt_lst[5]= [cx+R,cy-R,cz+R]
        pt_lst[6]= [cx+R,cy+R,cz+R]
        pt_lst[7]= [cx-R,cy+R,cz+R]
        x = pt_lst[:,0]
        y = pt_lst[:,1]
        z = pt_lst[:,2]
        # Face IDs
        vertices = [[0,1,2,3],[1,5,6,2],[3,2,6,7],[4,0,3,7],[5,4,7,6],[4,5,1,0]]
        
        tupleList = list(zip(x, y, z))
        poly3d = [[tupleList[vertices[ix][iy]] for iy in range(len(vertices[0]))] for ix in range(len(vertices))]
        face_color = 'y'
        if self.flg_plot_cell_faces == True:
            alpha_val = 0.5
        else:
            alpha_val = 0.0
        self.ax.add_collection3d(Poly3DCollection(poly3d, edgecolors= 'k',facecolors=face_color, linewidths=1, alpha=alpha_val))
        

     

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
    
    
    def plot_particles(self,plist,aspoints=True,scolor=None):
        
        p_count = 0
        sphere_facets = int(self.cfg.sphere_facets_text)
        p_start = int(self.cfg.particle_range_array[0])
        p_end = int(self.cfg.particle_range_array[1])
        theta = np.linspace(0, 2 * np.pi, sphere_facets)
        phi = np.linspace(0, np.pi, sphere_facets)
        theta, phi = np.meshgrid(theta, phi)
        pcolor = self.cfg.particle_color_text
        if aspoints == True:    
            self.ax.scatter(plist[:,1],plist[:,2],plist[:,3])
        else:
            for ii in plist:
                if (p_count >= p_start):
                    # Convert to Cartesian coordinates
                    x = ii.rx + ii.radius * np.sin(phi) * np.cos(theta)
                    y = ii.ry + ii.radius * np.sin(phi) * np.sin(theta)
                    z = ii.rz + ii.radius * np.cos(phi)
                    if ii.ptype == 1:
                        self.ax.plot_surface(x, y, z, color='blue',alpha=0.8)
                    else:
                        self.ax.plot_surface(x, y, z, color=pcolor,alpha=0.8)
                    #print(f"Particle {p_count} Loc: <{ii.rx:2f},{ii.ry:2f},{ii.rz:2f})>")
                    
                p_count +=1
                if(p_count > p_end):
                    break
                    

    def on_scroll(self, event):
        #print(event.button, event.step)
        
        # Check if the event is a scroll event
        if event.button == 'down':
            scale_factor = 1.1  # Increase the scale factor to zoom in more
        elif event.button == 'up':
            scale_factor = 0.9  # Decrease the scale factor to zoom out more
        else:
            scale_factor = 1.0

        # Get the current x and y limits of the axes
        x_limits = self.ax.get_xlim()
        y_limits = self.ax.get_ylim()
        z_limits = self.ax.get_xlim()

        # Calculate the new limits based on the scroll event
        x_range = (event.xdata - x_limits[0]) / (x_limits[1] - x_limits[0])
        y_range = (event.ydata - y_limits[0]) / (y_limits[1] - y_limits[0])
        z_Range = y_range
        new_x_limits = (
            event.xdata - (x_limits[1] - x_limits[0]) * scale_factor * x_range,
            event.xdata + (x_limits[1] - x_limits[0]) * scale_factor * (1 - x_range)
        )
        new_y_limits = (
            event.ydata - (y_limits[1] - y_limits[0]) * scale_factor * y_range,
            event.ydata + (y_limits[1] - y_limits[0]) * scale_factor * (1 - y_range)
        )
        

        # Update the x and y limits of the axes
        self.ax.set_xlim(new_x_limits)
        self.ax.set_ylim(new_y_limits)
        self.ax.set_zlim(new_y_limits)
        plt.pause(0.01)
