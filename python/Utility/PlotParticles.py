start_cell = 0
    end_cell = 0
    flg_plt_exists  = False
    toggle_flag = False
    cur_view_num = 0
    cur_file = ""
    flg_plot_cell_faces = False
    flg_plot_cells = False
    
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
