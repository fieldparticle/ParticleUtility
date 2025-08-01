import matplotlib as plt
import numpy as np
from mpl_interactions import ioff, panhandler, zoom_factory
import plotly.express as px
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os
from ConfigUtility import *

class PlotParticles():    
    
    start_cell = 0
    end_cell = 0
    flg_plt_exists  = False
    toggle_flag = False
    cur_view_num = 0
    cur_file = ""
    flg_plot_cell_faces = False
    flg_plot_cells = False
    particle_data = None
    item_cfg = None

    views = [('XY',   (90, -90, 0)),
        ('XZ',    (0, -90, 0)),
        ('YZ',    (0,   0, 0)),
        ('-XY', (-90,  90, 0)),
        ('-XZ',   (0,  90, 0)),
        ('-YZ',   (0, 180, 0))]   

    def create(self,itemcfg,parent):
        self.itemcfg = itemcfg
        self.parent = parent

    #******************************************************************
    # Save off data start the plot.
    #
    def plot(self,itemcfg,particle_data,file_name,view_num=None,cells_on=True):
        self.itemcfg = itemcfg
        self.particle_data = particle_data
        self.cur_file = file_name        
        self.set_up_plot()
        file_prefix = os.path.splitext(file_name)[0]
        self.test_file_name = file_prefix + ".tst"
        self.tstcfg = ConfigUtility(self.test_file_name)
        self.tstcfg.Create(self.parent.bobj.log,self.test_file_name)
        self.tst_side_length = self.itemcfg.cell_range
        self.do_plot()
        plt.show(block=False)
    #******************************************************************
    # Do the plot
    #    
    def do_plot(self,view_num=None):
        self.plot_particles(aspoints=False)
        if self.flg_plot_cells == True:
            for ii in range(1,self.tst_side_length+1):
                for jj in range(1,self.tst_side_length+1):
                    for kk in range(1,self.tst_side_length+1):
                        self.plot_cells(ii,jj,kk)

        self.end_plot()
        self.flg_plt_exists  = True


    #******************************************************************
    # Set up the plot
    #
    def set_up_plot(self):
        self.fig = plt.figure(1,figsize=(12, 10))
        self.ax = self.fig.add_subplot(projection='3d')
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)


    #******************************************************************
    # plot the particles
    #
    def plot_particles(self,aspoints=True,scolor=None):
        
        p_count = 0
        # Get the number facets for smoothness
        sphere_facets = self.itemcfg.sphere_facets
        # Get the start particle number
        p_start = self.itemcfg.particle_range[0]
        # Get the end particle number
        p_end = int(self.itemcfg.particle_range[1])
        # Set up the sphere data
        theta = np.linspace(0, 2 * np.pi, sphere_facets)
        phi = np.linspace(0, np.pi, sphere_facets)
        theta, phi = np.meshgrid(theta, phi)
        # Set the default color
        pcolor = self.itemcfg.particle_color
        # If plotting as points just do a scatter
        if aspoints == True:    
            self.ax.scatter(self.particle_data[:,1],self.particle_data[:,2],self.particle_data[:,3])
        # If doing spheres 
        else:
            # Traverse particle data
            for ii in self.particle_data:
                if (p_count >= p_start):
                    # Convert to Cartesian coordinates
                    x = ii.rx + ii.radius * np.sin(phi) * np.cos(theta)
                    y = ii.ry + ii.radius * np.sin(phi) * np.sin(theta)
                    z = ii.rz + ii.radius * np.cos(phi)
                    # If the particle is in collision use a different color
                    if ii.ptype == 1:
                        self.ax.plot_surface(x, y, z, color='blue',alpha=0.8)
                    # Else uese standar color
                    else:
                        self.ax.plot_surface(x, y, z, color=pcolor,alpha=0.8)
                    #print(f"Particle {p_count} Loc: <{ii.rx:2f},{ii.ry:2f},{ii.rz:2f})>")
                    
                p_count +=1
                if(p_count > p_end):
                    break
    #******************************************************************
    # plot the cells
    #                
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

    #******************************************************************
    # End plot processing
    #                
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

    #******************************************************************
    # Toggle viewing cell faces
    #
    def toggle_cell_face(self):
        if self.flg_plot_cell_faces == True:
            self.flg_plot_cell_faces = False
        else:
            self.flg_plot_cell_faces = True
        if self.flg_plot_cells == True:
            self.update_plot()
        else:
            print("Plotting cells is off.")

    #******************************************************************
    # Toggle viewing cells as lines
    #
    def toggle_cells(self):
        if(self.flg_plot_cells == True):
            self.flg_plot_cells = False
        else:
            self.flg_plot_cells = True
        self.update_plot()

    #******************************************************************
    # Set the view number
    #
    def set_view_num(self,viewnum):
        self.cur_view_num = viewnum


    def set_cell_toggle_flag(self, flag):
        self.toggle_flag = flag

    #******************************************************************
    # Close the plot if open
    #
    def close_plot(self):
        plt.close()

   
    def update_plot(self): 
        plt.cla()
        self.do_plot()
        plt.show(block=False)
        plt.pause(0.01)
        
        
    def side_value_changed(self,side_txt):
        if len(side_txt) < 2:
            return None
        self.start_cell = int(side_txt[0])
        self.end_cell = int(side_txt[1])
        
    def plot_view_changed(self,view):
        self.fig.canvas.draw()

    
        


    def get_side_length_txt(self):
        side_txt = f"{self.tst_side_length}:{self.tst_side_length}"
        
   
  