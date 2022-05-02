

import re



class Configuration:
    def __init__(self, id, xc1,zc1,xc2,zc2,xp1,zp1,xp2,zp2):
        self.id = id
        self.xc1 = xc1
        self.xc2 = xc2
        self.zc1 = zc1
        self.zc2 = zc2
        self.xp1 = xp1
        self.zp1 = zp1
        self.xp2 = xp2
        self.zp2 = zp2

    def get_formated_string(self,new_id:int)->str:
        return f'Configuration {new_id}\n{self.xc1:.0f},{self.zc1:.0f}\n{self.xc2:.0f},{self.zc2:.0f}\n{self.xp1:.0f},{self.zp1:.0f}\n{self.xp2:.0f},{self.zp2:.0f}\n'
    
class ForwardModellingConfigurations:
    def __init__(self,name,electrode_spacing):
        self.name = name
        self.unit_electrode_spacing=electrode_spacing
        self.all_configurations=[]
        self.material_resistivity=100
        self.max_current=1
        self.minimum_potential=0.001
        self.x_start=-320
        self.x_end=1120
        self.x_spacing=5
        self.z_start=0.1
        self.z_end=481
        self.z_spacing=5
        
    def add_configuration(self,config:Configuration)->None:
        self.all_configurations.append(config)
    
    def make_content(self)->str:
        s=f'{self.name}\n'
        s+='Number of configurations\n'
        s+=f'{len(self.all_configurations)}\n'
        s+='Unit electrode spacing\n'
        s+=f'{self.unit_electrode_spacing}\n'
        s+='Coordinates of electrodes (xc1,zc1,xc2,zc2,xp1,zp1,xp2,zp2)\n'
        new_id=1
        for c in self.all_configurations:
            s+=c.get_formated_string(new_id)
            new_id+=1
        s+='Starting and ending x-location to calculate sensitivity values, spacing\n'
        s+=f'{self.x_start:.2f},{self.x_end:.2f},{self.x_spacing:.2f}\n'
        s+='Starting and ending z-location to calculate sensitivity values, spacing\n'
        s+=f'{self.z_start:.2f},{self.z_end:.2f},{self.z_spacing:.2f}\n'
        s+='Material resistivity (ohm.m)\n'
        s+=f'{self.material_resistivity:.1f}\n'
        s+='Maximum current (Amp)\n'
        s+=f'{self.max_current:.4f}\n'
        s+='Minimum potential (mV)\n'
        s+=f'{self.minimum_potential:.3f}\n'
        return s


    def export(self, filename):
        with open(filename, 'w') as f:
        #with open(filename, 'w', newline='\r\n') as f:
            f.write(self.make_content())

    @classmethod
    def import_file(cls,filepath):
        regex_electrode_spacing = r"Unit electrode spacing\s*(?P<electrode_spacing>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        regex = r"Configuration\s*(?P<id>\d+)\s*(?P<xc1>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,\s*(?P<zc1>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*(?P<xc2>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,\s*(?P<zc2>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*(?P<xp1>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,\s*(?P<zp1>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*(?P<xp2>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,\s*(?P<zp2>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*"
        regex_start_end_spacing_x = r"Starting and ending x-location to calculate sensitivity values, spacing\s*(?P<start>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,(?P<end>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,(?P<spacing>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        regex_start_end_spacing_z = r"Starting and ending z-location to calculate sensitivity values, spacing\s*(?P<start>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,(?P<end>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s*,(?P<spacing>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        regex_material_resistivity = r"Material resistivity \(ohm\.m\)\s*(?P<value>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        regex_max_current =  r"Maximum current\s\(Amp\)\s*(?P<value>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        regex_minimum_potential = r"Minimum potential\s\(mV\)\s*(?P<value>[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"

        with open(filepath) as f:
            # read file
            file_as_string=f.read()
            # read array name on first line
            f.seek(0)
            name=f.readline()
            name=name.rstrip()

            def get_single_match_parameter(param_regex,name):
                matches=re.finditer(param_regex,file_as_string,re.MULTILINE)
                for match in matches:
                    return float(match.groupdict()[name])
                print(f'warning. expected parameter {name} not found')
                return None
            def get_three_match_parameter(param_regex,name1,name2,name3):
                matches=re.finditer(param_regex,file_as_string,re.MULTILINE)
                for match in matches:
                    return float(match.groupdict()[name1]),float(match.groupdict()[name2]),float(match.groupdict()[name3])
                print(f'warning. expected parameter {name1},{name2},or {name3} not found')
                return None
            # read unit electrode
            unit_electrode_spacing=get_single_match_parameter(regex_electrode_spacing,'electrode_spacing')
            config_model=ForwardModellingConfigurations(name, unit_electrode_spacing)

            config_model.material_resistivity=get_single_match_parameter(regex_material_resistivity,'value')
            config_model.max_current=get_single_match_parameter(regex_max_current,'value')
            config_model.minimum_potential=get_single_match_parameter(regex_minimum_potential,'value')
            config_model.x_start,config_model.x_end,config_model.x_spacing=get_three_match_parameter(regex_start_end_spacing_x,'start','end','spacing')
            config_model.z_start,config_model.z_end,config_model.z_spacing=get_three_match_parameter(regex_start_end_spacing_z,'start','end','spacing')



            #for matchNum, match in enumerate(match_electrode_spacing, start=1): 
            #    unit_electrode_spacing=match.groupdict()['electrode_spacing']
            
            
            matches = re.finditer(regex, file_as_string, re.MULTILINE)
            
            # read all 4 electrode configurations
            for matchNum, match in enumerate(matches, start=1):
                config_model.add_configuration(Configuration(float(match.groupdict()['id']),
                float(match.groupdict()['xc1']),
                float(match.groupdict()['zc1']),
                float(match.groupdict()['xc2']),
                float(match.groupdict()['zc2']),
                float(match.groupdict()['xp1']),
                float(match.groupdict()['zp1']),
                float(match.groupdict()['xp2']),
                float(match.groupdict()['zp2'])))
            return config_model



if __name__ == '__main__':
    # Test function used for filtering
    def is_config_ok(configuration:Configuration):
        if configuration.xc2==720:
            return True
        else:
            #print(f"skipping Configuration {item.id}")
            pass
        return False


    #read file
    config_model=ForwardModellingConfigurations.import_file('GD_1176.txt')
    print(f'Imported {len(config_model.all_configurations)} configurations')

    #filter
    new_list=[]
    for item in config_model.all_configurations:
        if is_config_ok(item):
            new_list.append(item)
    config_model.all_configurations= new_list

    #export new file
    config_model.export(f'GD_1176_modified_to_{len(config_model.all_configurations)}.txt')
    print(f'Exported {len(config_model.all_configurations)} configurations')

