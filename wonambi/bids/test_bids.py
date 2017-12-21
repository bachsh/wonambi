
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('gui', 'qt')


# In[123]:


from re import match, search
from json import load as json_load

from pathlib import Path


# In[171]:


def _read_tsv(filename):
    with filename.open() as f:
        hdr = f.readline()
        tsv = []
        for l in f:
            d = {k.strip(): v.strip() for k, v in zip(hdr.split('\t'), l.split('\t'))}
            tsv.append(d)
    return tsv        


def _match(filename, pattern):
    m = search(pattern, filename.stem)
    if m is None:
        return m
    else:
        return m.group(1)


# In[172]:


class bids_Core():
    def __init__(self, filename):
        self.filename = Path(filename)
        self.subject = _match(self.filename, 'sub-([a-zA-Z0-9]+)_')
        self.session = _match(self.filename, '_ses-([a-zA-Z0-9]+)_')
        self.run = _match(self.filename, '_run-([a-zA-Z0-9]+)_')
                
class bids_Tsv(bids_Core):
    def __init__(self, filename):
        super().__init__(filename)
        self.tsv = _read_tsv(self.filename)
    
class bids_Json(bids_Core):
    def __init__(self, filename):
        super().__init__(filename)
        with self.filename.open() as f:
            self.json = json_load(f)     
            
class bids_Channels(bids_Tsv):
    def __init__(self, filename):
        super().__init__(filename) 
        
        
class bids_Events(bids_Tsv):
    def __init__(self, filename):
        super().__init__(filename) 
    
    
class bids_Electrodes(bids_Tsv):
    def __init__(self, filename):
        super().__init__(filename)  
       
    
class bids_Modality(bids_Json):
    def __init__(self, filename):
        super().__init__(filename)      
        
        
filename = Path('/home/giovanni/tools/BIDS-examples/ieeg_visual/sub-01/ses-01/ieeg/sub-01_ses-01_task-visual_run-01_ieeg.json')
m = bids_Modality(filename) 

filename = Path('/home/giovanni/tools/BIDS-examples/ieeg_visual/sub-01/ses-01/ieeg/sub-01_ses-01_task-visual_run-01_channels.tsv')
c = bids_Channels(filename)  

filename = Path('/home/giovanni/tools/BIDS-examples/ieeg_visual/sub-01/ses-01/ieeg/sub-01_ses-01_task-visual_run-01_events.tsv')
e = bids_Events(filename)

filename = Path('/home/giovanni/tools/BIDS-examples/ieeg_visual/sub-01/ses-01/ieeg/sub-01_ses-01_acq-corrected_electrodes.tsv')
elec = bids_Electrodes(filename)        


t1 = bids_Json('/home/giovanni/tools/BIDS-examples/ieeg_visual/sub-01/ses-01/anat/sub-01_ses-01_T1w.json')


# In[173]:


dirname = Path('/home/giovanni/tools/BIDS-examples/ieeg_visual')


# In[174]:


from nibabel import load as ni_load
gii = ni_load('/home/giovanni/tools/BIDS-examples/ieeg_visual/sub-01/ses-01/anat/sub-01_ses-01_T1w_pial.R.surf.gii')
g = gii.darrays[0]


# In[180]:


class dir_Core():
    def __init__(self, dirname):
        self.dirname = Path(dirname)

class dir_Root(dir_Core):        
    def __init__(self, dirname):
        super().__init__(dirname)      

        self.participants = bids_Tsv(self.dirname / 'participants.tsv')
        self.subjects = []
        for participant in self.participants.tsv:
            self.subjects.append(dir_Core(self.dirname / participant['participant_id']))


# In[181]:


self = dir_Root('/home/giovanni/tools/BIDS-examples/ieeg_visual')


# In[183]:


self.subjects[0]


# In[178]:




