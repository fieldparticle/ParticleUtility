
from GenDataBase import *

class GenPQBData(GenDataBase):

    def __init__(self):
        super().__init__()




    def gen_data(self):
        self.gen_data_base()
        self.open_bin_file()
        
    def plot_particle_cell(self,file_name):
        self.plot_particle_cell_base(file_name)
    
    
    def place_particles(self,xx,yy,zz,row,col,layer,w_list):
        
        if(self.particles_in_cell_count > self.particles_in_cell ):
            return 2
        
        if (self.particle_count >= self.number_particles):
            return 3
        
        #print(f"particle: {self.particle_count}, xx={xx}, yy= {yy}, zz={zz}, layer= {layer}, row= {row} col= {col}")
        #                         |offset so no particle is in a cell with a zero in it|
        particle_struct = pdata()
        
        
        if(self.collsions_in_cell_count <= self.num_collisions_per_cell ):
            ry = 0.5 + 2.0*self.radius + self.center_line_length*col+yy
            self.collsions_in_cell_count+=2
            particle_struct.ptype = 1
        else:
            particle_struct.ptype = 0
            ry = 0.5 + self.radius + 0.15 * self.radius + self.center_line_length*col+yy

        rx = 0.5 + self.radius + 0.15 * self.radius + self.center_line_length*row+xx
        rz = 0.5 + self.radius + 0.15 * self.radius + self.center_line_length*layer+zz
        
        """
        if(self.collsions_in_cell_count <= self.num_collisions_per_cell ):
            rx = 0.5 + self.radius/2.0 + self.center_line_length*row+xx
            self.collsions_in_cell_count+=2
        else:
            rx = 0.5 + self.radius + 0.15 * self.radius + self.center_line_length*row+xx

        ry = 0.5 + self.radius + 0.15 * self.radius + self.center_line_length*col+yy
        rz = 0.5 + self.radius + 0.15 * self.radius + self.center_line_length*layer+zz
            #print(f"Particle Loc: <{rx:2f},{ry:2f},{rz:2f})>")
        """

        #if (self.number_particles%1000 == 0):
        #print(f"Current particle:{self.particle_count}")

        
        particle_struct.pnum = self.particle_count
        particle_struct.rx = rx
        particle_struct.ry = ry
        particle_struct.rz = rz
        particle_struct.radius = self.radius
        
        #packed_struct = bytearray(particle_struct)
        w_list.append(particle_struct)
        self.particle_count+=1
        self.particles_in_cell_count +=1
        return 0
        
    
    def do_cells(self):
        ret = 0
        self.w_list = []
        self.particle_count = 0
        for zz in range(self.cell_z_len-1):
            for yy in range(self.cell_y_len-1):
                for xx in range(self.cell_x_len-1):
                    self.collsions_in_cell_count = 0
                    self.particles_in_cell_count = 0
                    # Inside a single cell. Process single cell
                    for layer in range(self.particles_in_layers):
                        for col in range(self.particles_in_col):        
                            for row in range(self.particles_in_row):                            
                                ret = self.place_particles(xx,yy,zz,row,col,layer,self.w_list)
                                if ret == 3:
                                    self.write_bin_file(self.w_list)
                                    self.w_list.clear()
                                    return 0
                                if len(self.w_list) >= self.cfg.write_block_len:
                                    self.write_bin_file(self.w_list)
                                    self.w_list.clear()
        self.write_bin_file(self.w_list)
        self.w_list.clear()
        
                                    
        
    
