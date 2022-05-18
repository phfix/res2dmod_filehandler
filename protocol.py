
#hitta alla projekt
import glob
from math import ceil
# importing os.path module  
import os.path
import sqlite3
import copy
from pathlib import Path
import re
#import xml.dom.minidom
import xml.etree.ElementTree as ET

from forward_modeling_configurations import Configuration, ForwardModellingConfigurations


# key <-> grid coordinate
# key -> world coordinate
# key <-> other system coordinate 
#
# key: cablename, takeoutname



class Coordinate:

    def __init__(self, x,y,z, remote=False):
        self.x=x
        self.y=y
        self.z=z
        self.remote=remote

    def __str__(self):
        return f'<{self.x:.1f};{self.y:.1f};{self.z:.1f}>'

    def __eq__(self, other):
        if self.remote and other.remote:
            return True
        if self.remote or other.remote:
            return False
        return self.x==other.x and self.y==other.y and self.z==other.z

    def Info(self):
        print("Coordinate:",self.x,self.y,self.z,self.remote)


    def move(self,pos):
        if self.remote is not True:
            self.x += pos.x
            self.y += pos.y
            self.z += pos.z

    def scale(self,pos):
        if self.remote is not True:
            self.x *= pos.x
            self.y *= pos.y
            self.z *= pos.z

    def max(self, other):
        if other.remote:
            return
        if self.x<other.x:
            self.x=other.x
        if self.y<other.y:
            self.y=other.y
        if self.z<other.z:
            self.z=other.z

    def min(self, other):
        if other.remote:
            return
        if self.x>other.x:
            self.x=other.x
        if self.y>other.y:
            self.y=other.y
        if self.z>other.z:
            self.z=other.z


def GetLocalPath(lspath):
    #return lspath.replace('/home/root/protocols/','testsetup/')
    return lspath.replace('/home/root/protocols/','alingsås/')
    
def SafeExtract(element,name, safevalue=""):
    try:
        return element.find(name).text.strip()
    except:
        return safevalue

def SafeExtractAll(element,name):
    l=[]
    try:
        for e in element.findall(name):
            text=e.text.strip()
            if text:
                l.append( text)
    except:
        pass
    
    return l

def SafeExtracXYZ(element):
    itemx=element.findall("X")
    itemy=element.findall("Y")
    itemz=element.findall("Z")
    if len(itemx)+len(itemy)+len(itemz) == 0:
        return Coordinate(0,0,0, True)

    x=float(SafeExtract(element,"X",0))
    y=float(SafeExtract(element,"Y",0))
    z=float(SafeExtract(element,"Z",0))
    return Coordinate(x,y,z)

class MapElectrode:
    def __init__(self, key1,key2, pos, id):
        self.key1=key1
        self.key2=key2
        self.pos=pos
        self.id=id

class Electrode:

    def __init__(self,element):
        self.id=SafeExtract(element,"Id")
        self.name=SafeExtract(element,"Name")
        self.switchaddress=SafeExtract(element,"SwitchAddress")
        self.switchid=SafeExtract(element,"SwitchId")
        self.pos=SafeExtracXYZ(element)
        #print(self.name)
       # self.pos.Info()

    def move(self,pos):
        self.pos= self.pos.add(pos)

    def make_electrodes(self,allmapelectrodes, stationpos, cablename):
        p=copy.copy( self.pos)
        p.move(stationpos)
        me= MapElectrode(cablename, self.name,p, self.id )
        allmapelectrodes.append(me)


class Cable:

    def __init__(self, element):
        self.name=SafeExtract(element,"Name")
        self.takeouts=list()
        for electrode in element.findall("Electrode"):
            self.takeouts.append( Electrode(electrode))

    def move(self,pos):
        for electrode in self.takeouts:
            electrode.move(pos)

    def make_electrodes(self,allelectrodes, stationpos):
        for electrode in self.takeouts:
            electrode.make_electrodes(allelectrodes,stationpos, self.name)

    def iterate_electrodes(self,fn):
        l=[]
        for takeout in self.takeouts:
            l.append(fn(takeout))
        return l

class CreateStation:
    def __init__(self,element):
        #CreateStation
        self.name=SafeExtract(element,"Name")
        self.pos=SafeExtracXYZ(element)


class Spread:

    def __init__(self, file):
        self.file=file
        self.et = ET.parse(file)
        self.root = self.et.getroot()
        #print(ET.tostring(self.root, encoding='utf8').decode('utf8'))
        self.createstations=[]
        
        self.name = SafeExtract(self.root,"Name")
        for cs in self.root.findall("CreateStation"):
            self.createstations.append( CreateStation(cs))
        if len(self.createstations)==0:
            for cs in self.root.findall("Rollalong"):
                self.createstations.append( CreateStation(cs))
                break
        self.cables = list()
        for cable in self.root.findall("Cable"):
            self.cables.append( Cable(cable))
            

        #.tail #.text() #encoding='utf8'
        #self.name= self.root.findall("Spread/Name").tail #.text() #encoding='utf8'
        #print(self.name)

    def extent(self):
        largeint=1e6
        high=Coordinate(0,0,0,False)
        low=Coordinate(largeint,largeint,largeint,False)
        def min_max(electrode):
            high.max(electrode.pos)
            low.min(electrode.pos)
        self.iterate_electrodes(min_max)
        return Coordinate(high.x-low.x, high.y-low.y, high.z-low.z,False)

    def get_standard_step(self):
        step=Coordinate(0,0,0,False)
        for cs in self.createstations:
            step.max(cs.pos)
        return step

    def make_electrodes(self,allelectrodes, stationpos):
        for cable in self.cables:
            cable.make_electrodes(allelectrodes,stationpos)
    def iterate_electrodes(self,fn):
        l=[]
        for cable in self.cables:
            l.append(cable.iterate_electrodes(fn))
        return l



class Dipole:
    def __init__(self, e1,e2):
        self.e1 = e1
        self.e2 = e2

    @classmethod
    def extract_dipole(cls,txt):
        dipole_pattern= re.compile(r"(?P<e1>\d+)\s+(?P<e2>\d+)",re.MULTILINE)
        match=dipole_pattern.search(txt)
        if match:
            e1=int(match.groupdict()['e1'])
            e2=int(match.groupdict()['e2'])
            return Dipole(e1,e2)
        else:
            return None

class Measure:

    def __init__(self, measure):
        self.tx=[]
        for tx in measure.findall("Tx"):
            dp=Dipole.extract_dipole(tx.text)
            if dp:
                self.tx.append(dp)
        self.rx=[]
        for rx in measure.findall("Rx"):
            dp=Dipole.extract_dipole(rx.text)
            if dp:
                self.rx.append(dp)
            

class Protocol:

    def __init__(self, file):
        self.file=file
        self.et = ET.parse(file)
        self.root = self.et.getroot()
        self.name = SafeExtract(self.root,"Name")
        self.description = SafeExtract(self.root,"Description")

        self.spreadfiles=SafeExtractAll(self.root,"SpreadFile")

        self.sequence = list()
        for seq in self.root.findall("Sequence"):
            for measure in seq.findall("Measure"):
                self.sequence.append( Measure(measure))
        print("parse done")
    

    def get_configurations(self,spread,stationpos, electrode_spacing):
        fw=ForwardModellingConfigurations(self.name,electrode_spacing.x)
        all_electrodes=[]
        spread.make_electrodes(all_electrodes,stationpos)
        ae=ActualElectrodes(all_electrodes,electrode_spacing)
        for measure in self.sequence:
            for rx in measure.rx:
                for tx in measure.tx:
                    c1=ae.get_coordinate(tx.e1)
                    c2=ae.get_coordinate(tx.e2)
                    p1=ae.get_coordinate(rx.e1)
                    p2=ae.get_coordinate(rx.e2)
                    depth_scaling=-1
                    fw.add_configuration(Configuration(0,c1.x,c1.z*depth_scaling,c2.x,c2.z*depth_scaling,p1.x,p1.z*depth_scaling,p2.x,p2.z*depth_scaling))
        return fw

    def get_all_configurations(self,spread, stationposlist, electrode_spacing):
        fw=ForwardModellingConfigurations(self.name,electrode_spacing.x) 
        l=[]
        for pos in stationposlist:
            l.append(self.get_configurations(spread,pos,electrode_spacing))
        
        if l:
            configurations =[]
            for fw in l:
                configurations += fw.all_configurations
            # make unique
            configurations= list(set(configurations))
            fw.all_configurations=configurations
        return fw


class Station:

    def __init__(self, id, x,y,z):
        self.id=id
        self.pos= Coordinate(float(x),float(y),float(z))
        #print("station", self.id)

    def make_electrodes(self,spread, allelectrodes):
        spread.make_electrodes(allelectrodes,self.pos)


class ActualElectrodes:
    def __init__(self,electrode_list,electrode_spacing):
        self.electrode_list=electrode_list
        self.electrodes={}
        for electrode in electrode_list:
            self.electrodes[int(electrode.id)]=electrode
        self.electrode_spacing=electrode_spacing

    def get_coordinate(self,index):
        if index==0: #special remote
            return Coordinate(0,0,0,True)
        if index in self.electrodes:
            pos=copy.copy( self.electrodes[index].pos)
            pos.scale(self.electrode_spacing)
            return pos
        raise ValueError(f"Unknown electrode index {index} in protocol")
        

class Simulation:
    def __init__(self,protocol, spread, spacing,length):
        self.protocol = protocol
        self.spread=spread
        self.spacing = spacing
        self.length= length


    def create_configfile(self):
        spacing= Coordinate(self.spacing,1,1)
        area_to_cover=Coordinate(self.length,0,0)
        
        spread= Spread(self.spread)
        step=spread.get_standard_step()
        extent=spread.extent()
        start_stop_steps=int(extent.x/step.x)-1
        startpos=-start_stop_steps*step.x
        no_of_electrodes=area_to_cover.x/spacing.x
        count=ceil(no_of_electrodes/step.x)+2*start_stop_steps
        stationspos=[]
        
        for i in range(count):
            print("Station at", startpos)
            stationspos.append( Coordinate(startpos,0,0))
            startpos+=step.x
        
        print('extent:',extent)

        print('standard step:',step)
        p=Protocol(self.protocol)
        config_model=p.get_all_configurations(spread, stationspos,spacing)

        # Test function used for filtering
        def is_config_ok(configuration:Configuration):
            return configuration.is_inside(0,area_to_cover.x)
        #filter
        new_list=[]
        for item in config_model.all_configurations:
            if is_config_ok(item):
                new_list.append(item)
        config_model.all_configurations= new_list
        print("done")
        config_model.update_extent()
        config_model.export(f'{p.name}_{spread.name}_{spacing.x}m_spacing_0_{area_to_cover.x}m.txt')


class Task:

    def __init__(self,project, description, taskinfo):
        self.project = project
        self.taskinfo = {}
        for index in range(len(description)):
           self.taskinfo[description[index][0]]=taskinfo[index]
        self.taskID=int(self.taskinfo['ID'])
        # figure out what stations to make electrodes for
        #load stations
        c=self.project.GetDB().cursor()
        self.stations = {}
        #Get all stations with data 
        c.execute('''select distinct stations.ID,  PosX, PosY, PosZ from stations, Measures where stations.TaskID=%i AND stations.id=Measures.StationID ORDER BY PosX, PosY, PosZ,stations.ID;''' % self.taskID)
        for row in c:
            self.stations[row[0]] = Station(row[0],row[1],row[2],row[3])
        self.GetBaseReference()
        self.GetElectrodeSpacing()

        self.spread= self.GetSpread()


    def ExtractAllElectrodes(self):
        allelectrodes = list()
        for station in self.stations:
            self.stations[station].make_electrodes(self.spread,allelectrodes)
        for e in allelectrodes:
            e.taskid=self.taskID
            e.project=self.project.GetName()
            
        return allelectrodes

    def GetName(self):
        return self.taskinfo['Name']

    def GetBaseReference(self):
        es=self.taskinfo['BaseReference']
        regex = r"([^;]*);([^;]*);([^;]*)"
        pos=re.split(regex,es)
        return Coordinate(float(pos[1]),float(pos[2]),float(pos[3]))

    def GetElectrodeSpacing(self):
        es=self.taskinfo['ElectrodeSpacing']
        regex = r"([^;]*);([^;]*);([^;]*)"
        pos=re.split(regex,es)
        return Coordinate(float(pos[1]),float(pos[2]),float(pos[3]))

    
    def GetProtocolFileName(self):
        return GetLocalPath(self.taskinfo['ProtocolFile'])

    def GetSpreadFileName(self):
        return GetLocalPath(self.taskinfo['SpreadFile'])


    def GetSpread(self):
        return Spread(self.GetSpreadFileName())

    def GetProtocol(self):
        return Spread(self.GetProtocolFileName())


class Project:

    def __init__(self, databasefile):
            self.databasefile=databasefile
            self.folder=os.path.dirname(databasefile) 
            self.projectdirname= os.path.basename(self.folder)
            try:
                with open(os.path.join(self.folder, 'project_name.txt'), 'r') as namefile:
                    self.name = namefile.read().replace('\n', '')

            except IOError:
                self.name=self.projectdirname

            self.db = None
            #print(self.databasefile)
            #print(self.folder)
            #print(self.projectdirname)
            #print(self.name)
            self.GetTasks()

    def GetName(self):
        return self.name

    def GetDB(self):
        if self.db is None:
            self.db = sqlite3.connect(self.databasefile)
        return self.db

    def CloseDB(self):
        if self.db is not None:
            self.db.close()
        self.db = None


    def GetTasks(self):
            c=self.GetDB().cursor()
            self.tasks = {}
            c.execute('''
                CREATE VIEW IF NOT EXISTS [tasksettingspiv]
                AS
                SELECT 
                    [TaskSettings].[key1] AS [taskid], 
                    MAX (CASE WHEN [Setting] = 'ProtocolFile' THEN [value] ELSE NULL END) AS [ProtocolFile], 
                    MAX (CASE WHEN [Setting] = 'ElectrodeSpacing' THEN [value] ELSE NULL END) AS [ElectrodeSpacing], 
                    MAX (CASE WHEN [Setting] = 'BaseReference' THEN [value] ELSE NULL END) AS [BaseReference], 
                    MAX (CASE WHEN [Setting] = 'SpreadFile' THEN [value] ELSE NULL END) AS [SpreadFile]
                FROM   [TaskSettings]
                GROUP  BY [taskid];''')
            c.execute('''
                SELECT 
                    [tasks].[id], 
                    [tasks].[name], 
                    [tasksettingspiv].[ProtocolFile], 
                    [tasksettingspiv].[ElectrodeSpacing], 
                    [tasksettingspiv].[BaseReference], 
                    [tasksettingspiv].[SpreadFile]
                FROM   [tasks],
                    [tasksettingspiv]
                WHERE  [tasks].[id] = [tasksettingspiv].[taskid];''')
            
            for row in c:
                self.tasks[row[1]] = Task(self,c.description,row)

            self.CloseDB()


    def GetTaskNames(self):
        names =list()
        for index  in self.tasks:
            names.append(self.tasks[index].GetName())
        return names


    def ExtractAllElectrodes(self):
        mapelectrodes =list()
        for index  in self.tasks:
            mapelectrodes.extend(self.tasks[index].ExtractAllElectrodes())
        return mapelectrodes

class MultiProjectSet:

    def __init__(self, folder):
        searchstring=os.path.join(folder,"*/project*.db")
        dirList = glob.glob(searchstring)
        self.projects = list()

        for d in dirList:
            print(d)
            self.projects.append(Project(d))
        print(f"found {len(self.projects)} project in folder search from  {searchstring}")
            
    def GetAllTaskNames(self):
        names = list()
        for p in self.projects:
            names.extend(p.GetTaskNames())
        return names

    def GetAllElectrodes(self):
        mapelectrodes = list()
        for p in self.projects:
            mapelectrodes.extend(p.ExtractAllElectrodes())
        return mapelectrodes


class Datum:

    def __init__(self,idrow,name, pos,name2):
        self.id=idrow
        self.name= name
        self.name2= name2
        self.pos= pos

class Gpsdata:

    def __init__(self, path, name2):
        text_file = open(path, "r")
        lines=text_file.readlines() 
        self.mapinfo= {}
        for line in lines:
            items=line.split()
            self.mapinfo[items[4]]=Datum(items[0], items[4],Coordinate(items[1],items[2],items[3]),name2)

        print("FILE read %s" %path)
        print(" len= %i" % len(self.mapinfo))


        # RBUS = Resistivity Bottom Up Stream (32 points) BU
        # RBNS = Resistivity Bottom Down Stream (32 points) BD
        # RMUS = Resistivity Middle Up Stream (32 points) MU
        # RMNS = Resistivity Middle Down Stream (32 points) MD
        # RTUS = Resistivity Top Up Stream (32 points) CU
        # RTNS = Resistivity Top Down Stream (32 points) CD
        # RVUS = Resistivity Left Up Stream (8 points) LU
        # RVNS = Resistivity Left Down Stream (8 points) LD
        # RHUS = Resistivity Right Up Stream (8 points) RU
        # RHNS = Resistivity Right Down Stream (8 points) RD

def test_mapping():
    #filelist = [("RBUS", "BU"),("RBNS","BD"),("RMUS","MU"),("RMNS","MD"),("RTUS","CU"),("RTNS","CD"),("RVUS","LU"),("RVNS","LD"),("RHUS","RU"),("RHNS","RD")]
    filelist = []
    mapping = {}
    for f in filelist:
        data=Gpsdata("readcoordinates/%s.txt" % f[0], f[1])
        mapping.update(data.mapinfo)

    db=sqlite3.connect("alingsås_map.db")
    conn= db.cursor()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS [map](
    [id] INTEGER PRIMARY KEY AUTOINCREMENT, 
    [linenumber] INTEGER, 
    [name] TEXT, 
    [name2] TEXT, 
    [PosX] REAL DEFAULT 0, 
    [PosY] REAL DEFAULT 0, 
    [PosZ] REAL DEFAULT 0,
    UNIQUE([name]));''')
    regex = r"[0-9]+"
    re_int = re.compile(regex)

    for m in mapping:
        #fix mapping 
        numbers=re_int.findall(mapping[m].name)
        name2=mapping[m].name2
        if len(numbers)>0:
            takeoutnumber= numbers[-1]
            name2='{}-{}'.format(name2, takeoutnumber)
        #,mapping[m].name2
        conn.execute('INSERT OR REPLACE INTO map(linenumber, name, name2, PosX,PosY,PosZ) VALUES (?,?,?,?,?,?);', [ mapping[m].id,mapping[m].name,name2,mapping[m].pos.x ,mapping[m].pos.y,mapping[m].pos.z])
        #print( mapping[m].id,mapping[m].name,mapping[m].name2,mapping[m].pos.x ,mapping[m].pos.y,mapping[m].pos.z)

    db.commit()


    #x=MultiProjectSet("testdata")
    x=MultiProjectSet("alingsås")
    mapelectrodes= x.GetAllElectrodes()
    key2list= ( e.key2 for e in mapelectrodes )
    key2list=list(set(key2list))
    key2list.sort()

    conn.execute('''
    CREATE TABLE IF NOT EXISTS [source](
    [id] INTEGER PRIMARY KEY AUTOINCREMENT, 
    [projectname] TEXT,
    [taskid] INTEGER,
    [key1] TEXT, 
    [key2] TEXT, 
    [PosX] REAL DEFAULT 0, 
    [PosY] REAL DEFAULT 0, 
    [PosZ] REAL DEFAULT 0
    );''')



    for m in mapelectrodes:
        conn.execute('INSERT OR REPLACE INTO source(projectname, taskid,key1, key2, PosX,PosY,PosZ) VALUES (?,?,?,?,?,?,?);', 
        [ m.project,m.taskid,m.key1,m.key2,
        m.pos.x ,m.pos.y,m.pos.z])
        #print( mapping[m].id,mapping[m].name,mapping[m].name2,mapping[m].pos.x ,mapping[m].pos.y,mapping[m].pos.z)
    db.commit()

    db.close()
    #for item in key2list:
    #    print(item)

    # ide projektnamn, projektunikid, taskname, taskid, spreadfile, spreadname, cablename, electrodename, spreadpos, gridpos, worldpos, stationid


if __name__ == '__main__':
    simulations=[
        Simulation('Wenner4x21.xml','4X21.xml',2,500), #2m spacing, 0-500m
        Simulation('Wenner4x21.xml','4X21.xml',5,500), #5m spacing, 0-500m
        Simulation('Wenner4x21.xml','4X21.xml',10,500),#10m spacing, 0-500m
        Simulation('Gradient_XL4X21.xml','4X21.xml',2,500),
        Simulation('Gradient_XL4X21.xml','4X21.xml',5,500),
        Simulation('Gradient_XL4X21.xml','4X21.xml',10,500)]
    for s in simulations:
        s.create_configfile()