from utilities import *
import random
from GenDataBase import *

class GenPQBData(GenDataBase):

    do_max_scale = False
    def __init__(self):
        super().__init__()

    def gen_random_numbers_in_range(self,low, high, n):
        return random.sample(range(low, high), n)
    
    def sort_write_random(self):
        plist = self.read_all_particle_data(self.test_bin_name)
        plist.sort(key=lambda x: x.pnum)
        self.open_bin_file()
        self.write_bin_file(plist)
        self.close_bin_file()


    def calculate_test_properties(self):
        try :
            print(self.index)
            self.collision_density      = float(self.select_list[self.index]["cdens"])
            self.number_particles       =  int(self.select_list[self.index]["tot"])
            self.radius                 = float(self.select_list[self.index]["radius"])
            self.sepdist                =  float(self.itemcfg.particle_separation)
        except BaseException as e:
            
            raise BaseException(f"calculate_test_properties Key error in record:{e}")
        # get diameter
        D = (2.0*self.radius)
        # how many particle fit in the 1.0 square cell
        subcell = math.floor(1.0/D)
        # how long is this numebr of particles
        len_parts = subcell*D

        # if the len is greater than 1.0 then remove particles unit there is some space left
        while len_parts >= 0.99:
            len_parts -= D

        # What is the maximum number of particle that can fit
        self.particles_in_row = round(len_parts/D)

        subcell = 1.0/self.particles_in_row
        dist =(subcell-2.0*self.radius) 
        self.sepdist = dist/2.0

        self.center_line_length     = 2.0*self.sepdist+2.0*self.radius

        self.particles_in_row       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_col       = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_layers    = int(math.floor(1.00 /self.center_line_length))
        self.particles_in_cell      = int(self.particles_in_row*self.particles_in_col*self.particles_in_layers)
        self.cell_occupancy_list_size   = self.particles_in_cell+10
        self.tot_num_cells              = int(self.number_particles / self.particles_in_cell)
        self.num_collisions_per_cell    = int(self.particles_in_cell*self.collision_density)
        
        # Can't have odd number of particles in collsions 
        # Calculations here are based on particles in collsion not particle pairs
        if self.num_collisions_per_cell % 2 != 0:
            self.num_collisions_per_cell+=1
       
        self.tot_num_collsions          = self.num_collisions_per_cell*self.tot_num_cells 
        self.side_length                = self.calc_side_length(self.number_particles,self.particles_in_cell)+1
        self.side_length_count          = self.side_length+1
        self.cell_x_len                 = self.side_length
        self.cell_y_len                 = self.side_length
        self.cell_z_len                 = self.side_length
      
        self.set_file_name = "{:03d}CollisionDataSet{:d}X{:d}X{:d}".format(self.index,self.number_particles,self.tot_num_collsions,self.side_length)
        self.test_file_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.tst'
        self.test_bin_name = self.itemcfg.data_dir + '/' + self.set_file_name + '.bin'
        self.report_file = self.itemcfg.data_dir + '/' + self.set_file_name 

        self.log.log(self,f"Collsion Density: { self.collision_density},Number particles:{self.number_particles},Radius: {self.radius}, Separation Dist: {self.sepdist:.4f}, Center line length: {self.center_line_length:.2f}")
        self.log.log(self,f"Particles in row: {self.particles_in_row}, Particles in Column: {self.particles_in_col}, Particles per cell: {self.particles_in_cell}")
        self.log.log(self,f"Cell array size: {self.cell_occupancy_list_size }")
        return 0


    def place_particles(self,xx,yy,zz,row,col,layer,w_list):

        
        # If particle cont is greater than the required numbe of particles return 3 to end the
        if (self.particle_count >= self.number_particles):
            return 3

        # IF number collsions met return 2
        if(self.particles_in_cell_count > self.particles_in_cell ):
            return 2
        
        # Switch for the range function
        if(self.do_max_scale == True):
            self.do_max_scale = False
        else:
            self.do_max_scale = True


        particle_struct = pdata()
        #print(f"particle: {self.particle_count}, xx={xx}, yy= {yy}, zz={zz}, layer= {layer}, row= {row} col= {col}")
        #                         |offset so no particle is in a cell with a zero in it|
       
        subcell = 1.0/self.particles_in_row
        dist =(subcell-2.0*self.radius) 
        sep = dist/2.0

        self.center_line_length     = 2.0*sep+2.0*self.radius
        self.switch_col = False
        odd_colum = 0
        if col == 0:
            odd_colum = 0
            self.switch_col = False
        else:
            odd_column = col%2
            self.switch_col  = True

        # If more colsions are needed
        if(self.collsions_in_cell_count < self.num_collisions_per_cell):
            if col%2:
                rx = 0.5 + sep + 0.25*self.radius + self.center_line_length*col+xx
                self.collsions_in_cell_count+=1
                self.collision_count+=1
                particle_struct.ptype = 1
                self.switch_col = False
            else:
                rx = 0.5 + sep + self.radius + self.center_line_length*col+xx
                self.collsions_in_cell_count+=1
                self.collision_count+=1
                particle_struct.ptype = 1
                self.switch_col = True
        else:
            particle_struct.ptype = 0
            rx = 0.5 + sep + self.radius + self.center_line_length*col+xx


        ry = 0.5 + sep + self.radius + self.center_line_length*row+yy        
        rz = 0.5 + sep + self.radius + self.center_line_length*layer+zz
    
        if round(rx) == 1 and round(ry) == 1 and round(rz) == 1:
            self.collsion_count_check = self.collsions_in_cell_count
        


        #print(f"row{row}:col{col} <{rx},{ry},{rz}> Cell:<{round(rx)},{round(ry)},{round(rz)}>")
        if self.itemcfg.particle_enumeration == 'random':
            particle_struct.pnum = self.rand_data[self.particle_count]

        elif self.itemcfg.particle_enumeration == 'scale':
            if self.do_max_scale == True:
                self.last_max_scale-=1
                particle_struct.pnum = self.last_max_scale
            else:
                self.last_min_scale+=1
                particle_struct.pnum = self.last_min_scale
            
        elif self.itemcfg.particle_enumeration == 'sequential':    
            particle_struct.pnum = self.particle_count + 1    

        particle_struct.rx = rx
        particle_struct.ry = ry
        particle_struct.rz = rz
        particle_struct.radius = self.radius
        w_list.append(particle_struct)
        self.particle_count+=1
        self.particles_in_cell_count +=1

        if self.old_rx < rx:
            self.old_rx = rx
        if self.old_ry < ry:
            self.old_ry = ry
        if self.old_rz < rz:
            self.old_rz = rz
        self.max_cell_location = [round(self.old_rx),round(self.old_ry),round(self.old_rz)]
        return 0
    #******************************************************************
    # Calulate the cell and particle propeties of the study
    #
    #     
    #******************************************************************
    def gen_data_base(self,index,progress_callback=None):
        self.index = index
        if(self.calculate_test_properties() != 0):
            return
        if self.itemcfg.test_files_only == False:
            self.create_bin_file()  
            self.collsion_count_check = 0
            ret = self.do_cells(progress_callback)
            self.close_bin_file()
        
        self.write_test_file()
        col_ary_size = self.cell_occupancy_list_size
        if self.itemcfg.particle_enumeration == 'random':
            self.sort_write_random()
        pu = ParticleUtilities(self.side_length,col_ary_size)
        print("=========================================================\n")
        print(f"max_cell_location = <{self.max_cell_location[0]},{self.max_cell_location[0]},{self.max_cell_location[0]}>")
        cell_index = pu.ArrayToIndex(self.max_cell_location)
        print(f"max_cell_index = <{cell_index}> total particles ")
        print(f"Total Particles: {self.particle_count} Colliding Particles:{self.num_collisions_per_cell}. Collsion pairs:{self.num_collisions_per_cell/2}")
        print("=========================================================\n")
        return ret    
    
    #******************************************************************
    # Iterate though the cells and place partiucles 
    #
    #     
    #******************************************************************
    def do_cells(self,progress_callback):
        self.old_rx = 0.0
        self.old_ry = 0.0
        self.old_rz = 0.0
        if self.itemcfg.particle_enumeration == 'random':
            self.rand_data = self.gen_random_numbers_in_range(1, self.number_particles+1, self.number_particles)    
        if self.itemcfg.particle_enumeration == 'scale':
            self.last_max_scale = self.number_particles+1

        ret = 0
        self.w_list = []
        self.particle_count = 0
        self.add_null_particle(self.w_list)
        ########################################################
        # This only happens here. The side_length is n
        # but since cells start at zero they go from 0 to n-1
        z_range = self.cell_z_len-1
        y_range = self.cell_y_len-1
        z_range = self.cell_x_len-1
        
        ########################################################
        for zz in range(z_range):
            ppc = float(self.particle_count/self.number_particles)*100.0
            if progress_callback!= None:
                progress_callback.emit(ppc)
            else:
                print(f"{ppc:.2f}")
            for yy in range(y_range):
                for xx in range(z_range):
                    self.collsions_in_cell_count = 0
                    self.particles_in_cell_count = 0
                    # Inside a single cell. Process single cell
                    for layer in range(self.particles_in_layers):
                        for row in range(self.particles_in_row): 
                            for col in range(self.particles_in_col):        
                                if self.flg_stop == True:
                                    return 1
                                ret = self.place_particles(xx,yy,zz,row,col,layer,self.w_list)
                                if ret == 3:
                                    if len(self.w_list) > 0:
                                        self.write_bin_file(self.w_list)
                                        print(f"{self.collsion_count_check}")
                                    return 0
                                if len(self.w_list) >= self.itemcfg.write_block_len:
                                    self.write_bin_file(self.w_list)
                                    self.w_list.clear()
        self.write_bin_file(self.w_list)
        return 0