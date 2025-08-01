
from GenDataBase import *

class GenPQBData(GenDataBase):

    def __init__(self):
        super().__init__()

    def place_particles(self,xx,yy,zz,row,col,layer,w_list):
        
        skip_flag = False
        if(self.particles_in_cell_count > self.particles_in_cell ):
            return 2
        
        if (self.particle_count >= self.number_particles):
            return 3
        
        particle_struct = pdata()
        #print(f"particle: {self.particle_count}, xx={xx}, yy= {yy}, zz={zz}, layer= {layer}, row= {row} col= {col}")
        #                         |offset so no particle is in a cell with a zero in it|
       
        
        if(self.collsions_in_cell_count <= self.num_collisions_per_cell):
            rx = 0.5 + 2.0*self.radius + self. particle_separation * self.radius + col*(self.inter_particle_distance+2.0*self.radius)+xx
            self.collsions_in_cell_count+=2
            particle_struct.ptype = 1
        else:
            particle_struct.ptype = 0
            rx = 0.5 + self.radius + self. particle_separation * self.radius + col*(2.0*self.inter_particle_distance+2.0*self.radius)+xx

        ry = 0.5 + self.radius + self. particle_separation * self.radius + row*(2.0*self.inter_particle_distance+2.0*self.radius)+yy
        rz = 0.5 + self.radius + self. particle_separation * self.radius + layer*(2.0*self.inter_particle_distance+2.0*self.radius)+zz
        #rz = 0.5 + self.radius + self. particle_separation * self.radius + self.center_line_length*layer+zz
    
        particle_struct.pnum = self.particle_count
        particle_struct.rx = rx
        particle_struct.ry = ry
        particle_struct.rz = rz
        particle_struct.radius = self.radius
        w_list.append(particle_struct)
        self.particle_count+=1
        self.particles_in_cell_count +=1
        return 0
        
    
    def do_cells(self,thread_worker=None):
        ret = 0
        self.w_list = []
        self.particle_count = 0

        # Calulate distances
        self. particle_separation = self.itemcfg.particle_separation
        self.size_in_row = 1.0/self.particles_in_row #C
        self.center_particle_distance = self.size_in_row-2*self.radius #d
        self.inter_particle_distance = self.center_particle_distance/2.0 #S

        # Add zeroth particle
        empty_struct = pdata()
        self.w_list.append(empty_struct)
        self.particle_count

        # Run thorough all of the dimensions and add particles
        for zz in range(self.cell_z_len-1):
            ppc = float(self.particle_count/self.number_particles)*100.0
            if  thread_worker != None:
                thread_worker.emit(ppc)
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
                                    if len(self.w_list) > 0:
                                        self.write_bin_file(self.w_list)
                                    return 0
                                if len(self.w_list) >= self.itemcfg.write_block_len:
                                    self.write_bin_file(self.w_list)
                                    self.w_list.clear()
        self.write_bin_file(self.w_list)
        
        
                                    
        
    
