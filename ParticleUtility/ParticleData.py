class ParticleData():

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
