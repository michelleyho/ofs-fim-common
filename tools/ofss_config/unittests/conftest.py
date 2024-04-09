import pytest
import configparser
import collections
import yaml

@pytest.fixture
def monkeypatch_env_rootdir(monkeypatch):
   monkeypatch.setenv("sample_rootdir", "imaginary/path")

@pytest.fixture
def ofss_project():
   data = {
      "ofs" : [{
         "settings":{
         "platform" : "asda",
		   "family" : "asdsa",
		   "fim" : "asdsa",
		   "part" : "adssa",
		   "device_id" : 1234,
		   "p_clk" : 123,
         }
      }],
      "pcie": [{'pcie1':None},{'pcie2':None}, {'pcie3':None}], 
      "hssi": [{'hssi1':None},{'hssi2':None}, {'hssi3':None}], 
      "mem": [{'mem1':None},{'mem2':None}, {'mem3':None}], 
      "sim_mem": [{'sim_mem1':None}], 
   }

   return data

@pytest.fixture
def ofss_data():
   parser = configparser.ConfigParser()
   parser['DEFAULT'] = {'Sampledefault': '123'}
   parser['ip'] = {'Sampleip': 'ip_123'}
   parser['include'] = {'some/path/A':'n/a', 'some/path/B':'n/a', '"$SAMPLE_ROOTDIR"/c':'n/a'}
   parser['key_a'] =  {'answer': 'yes'}
   parser['key_b'] =  {'answer': 'yes'}
   parser['key_c'] =  {'answer': 'yes'}
   
   return parser

@pytest.fixture
def sample_ofs_ip_configurations():
   config = None
   with open('unittests/ofs_settings_n6001.yml') as yIn:
      config = yaml.safe_load(yIn)

   return config

@pytest.fixture
def ofs_config():
   config = {}
   config["settings"] = {
      'platform': "platform_abc",
      'family': "agilex",
      'fim': "base_x123",
      'part': "ABCDEFGH",
      'device_id': "1234",
   }

   return config

@pytest.fixture
def pcie_config():
   config = {}
   config["settings"] = {"output_name": "pcie_sample"}
   config["pf0"] = {
      "num_vfs": 1234,
      "bar0_address_width": 64,
      "vf_bar0_address_width": 20,
   }

   return config

@pytest.fixture
def pcie_core_params():
   core_params = {
      "core16_xxx": "x",
      "core16_yyyy": "y",
      "core16_z" : 5,
      "core16_1234": 1234,
   }

   return core_params

@pytest.fixture
def sample_param_dict():
   param_dict = {
   "core16_{func_num}_pci_type0_vendor_id_hwtcl": [0xFEEDBEEF, "pci_type0_vendor_id"],
   "core16_{func_num}_pci_type0_vendor_id_user_hwtcl": ["0xDEADBEEF", "pci_type0_vendor_id"],
   #"core16_{func_num}_pci_type0_device_id_hwtcl": ["0xDEADBEEF", "pci_type0_device_id"], 
   #"core16_{func_num}_pci_msix_table_size_hwtcl": 1337,
   "core16_{func_num}_pci_msix_table_offset_hwtcl": 1337,
   }

   return param_dict