import pytest
import gen_ofs_settings
import argparse
import random
import os
import sys
import logging
from contextlib import nullcontext

LOGGER = logging.getLogger(__name__)
import collections
from unittest import mock
from contextlib import nullcontext as does_not_raise

from pcie_ip import PCIe as PCIe
from ip_params.pcie_ss_parameters import default_component_params
from importlib.machinery import SourceFileLoader

@pytest.mark.parametrize(
        "pcie_component",
        [
            ("pcie_ss"),
            ("intel_pcie_ss_axi"),
        ],
)
def test_pcie_constructor(ofs_config, tmpdir, pcie_config, pcie_component):
    pcie_config['settings']['ip_component'] = pcie_component
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    assert pcie_inst.ip_type == "PCIe"
    assert pcie_inst.pcie_config == pcie_config
    assert pcie_inst.ip_component == pcie_component
    assert pcie_inst.ip_path == os.path.join(tmpdir, "ipss", "pcie", "qip")
    assert not pcie_inst.pf_vf_count
    assert pcie_inst.num_pfs == 0
    assert pcie_inst.num_vfs == 0
    assert not pcie_inst.all_pfs
    assert pcie_inst.pcie_gen is None
    assert pcie_inst.pcie_instances is None
    assert not pcie_inst.pcie_lane_width
    assert pcie_inst.PCIE_AVAILABLE_LANES == 16
    assert pcie_inst.pcie_instances_enabled == 1
    assert not pcie_inst.ip_component_params
   
@pytest.mark.parametrize(
        "pcie_component",
        [
            ("pcie_ss"),
            ("intel_pcie_ss_axi"),
        ],
)
def test_get_ip_settings_with_default(ofs_config, pcie_config, tmpdir, pcie_component):
    pcie_config['settings']['ip_component'] = pcie_component

    expected_modules = SourceFileLoader(
            f"pcie", f"ip_params/{pcie_component}_parameters.py"
        ).load_module()
    
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir) 
    pcie_inst.get_ip_settings()

    assert pcie_inst.ip_component_params == expected_modules.default_component_params
    assert pcie_inst.pcie_gen is None
    assert pcie_inst.pcie_instances is None
    assert pcie_inst.pcie_instances_enabled  == 1
    assert not pcie_inst.ip_preset 

def test_get_ip_settings_with_pcie_gen(ofs_config, pcie_config, tmpdir):
    rand_gen_num = random.randrange(1,10)
    LOGGER.info(f"Setting pcie gen to random number: {rand_gen_num}")
    pcie_config['settings']['pcie_gen'] = rand_gen_num
   
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir) 
    pcie_inst.get_ip_settings()

    assert pcie_inst.pcie_gen == rand_gen_num
   
def test_get_ip_settings_with_pcie_instances(ofs_config, pcie_config, tmpdir):
    rand_inst= random.randrange(1,10)
    LOGGER.info(f"Setting pcie instances to random number: {rand_inst}")
    pcie_config['settings']['pcie_instances'] = rand_inst
   
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir) 
    pcie_inst.get_ip_settings()

    assert pcie_inst.pcie_instances == rand_inst
    assert pcie_inst.pcie_lane_width == int(16/rand_inst)

def test_get_ip_settings_with_pcie_inst_enabled(ofs_config, pcie_config, tmpdir):
    rand_pcie_inst_enabled = random.randrange(2,10)
    LOGGER.info(f"Setting pcie gen to random number: {rand_pcie_inst_enabled}")
    pcie_config['settings']['pcie_instances_enabled'] = rand_pcie_inst_enabled
   
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir) 
    pcie_inst.get_ip_settings()

    assert pcie_inst.pcie_instances_enabled  == rand_pcie_inst_enabled
 
def test_get_ip_settings_with_pcie_lane_width(ofs_config, pcie_config, tmpdir):
    rand_pcie_lane_width = random.randrange(64, 512, 64)
    LOGGER.info(f"Setting pcie gen to random number: {rand_pcie_lane_width}")
    pcie_config['settings']['pcie_lane_width'] = rand_pcie_lane_width
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir) 
    pcie_inst.get_ip_settings()

    assert pcie_inst.pcie_lane_width == rand_pcie_lane_width

def test_get_ip_settings_with_preset(ofs_config, pcie_config, tmpdir):
    pcie_config['settings']['preset'] = "sample_preset"
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir) 
    pcie_inst.get_ip_settings()

    assert pcie_inst.ip_preset == "sample_preset"
    assert not pcie_inst.ip_component_params 


def test_check_configurations_valid_num_pfs(ofs_config, pcie_config, tmpdir, mocker):
    num_pfs = random.randrange(1,8)
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count): 
        pcie_inst.check_configuration()
        
@pytest.mark.parametrize('num_pfs', [0, random.randrange(9,20)])
def test_check_configurations_invalid_num_pfs(ofs_config, pcie_config, tmpdir, num_pfs, mocker):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1


def test_check_configurations_invalid_pfs(ofs_config, pcie_config, tmpdir, mocker):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    num_pfs = random.randrange(2,8)
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

def test_check_configruations_f2000x_pf0_with_vfs(ofs_config, pcie_config, tmpdir):
    ofs_config['settings']['platform'] = "f2000x"
 
    pcie_config['pf0']['num_vfs'] = 1
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    num_pfs = 1
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), mock.patch.object(pcie_inst, "ip_output_name", new="soc_pcie_ss"): 
        pcie_inst.check_configuration()

def test_check_configruations_f2000x_pf0_no_vfs(ofs_config, pcie_config, tmpdir):
    ofs_config['settings']['platform'] = "f2000x"
 
    pcie_config['pf0']['num_vfs'] = 0
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    num_pfs = 1
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), mock.patch.object(pcie_inst, "ip_output_name", new="soc_pcie_ss"): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

def test_check_configurations_n6001_pf0_no_vfs_with_pf1(ofs_config, pcie_config, tmpdir, mocker):
    ofs_config['settings']['platform'] = "n6001"
    pcie_config['pf0']['num_vfs'] = 0
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    num_pfs = random.randrange(2,8)
    for n in range(num_pfs):
        if f'pf{n}' not in pcie_config:
            pcie_config[f'pf{n}'] = {}
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count): 
        pcie_inst.check_configuration()


def test_check_configurations_n6001_pf0_no_vfs_no_pf1(ofs_config, pcie_config, tmpdir, mocker):
    ofs_config['settings']['platform'] = "n6001"
    pcie_config['pf0']['num_vfs'] = "0"
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    num_pfs = 1
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

def test_process_vfs_num_vfs_greater_than_2000(ofs_config, pcie_config, tmpdir):
    pcie_config['pf0']['num_vfs'] = 5000
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
   
    
   
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        pcie_inst.process_vfs('pf0')

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


@pytest.mark.parametrize(
        'pcie_gen, pcie_instances',
        [
            (["4","1"]),
            (["5","1"]),
        ]
)
def test_check_configuration_valid_pcie_gen_num_instance(ofs_config, pcie_config, tmpdir, pcie_gen, pcie_instances):
    num_pfs = random.randrange(1,8)
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), mock.patch.object(pcie_inst, "pcie_gen", new=pcie_gen), mock.patch.object(pcie_inst, "pcie_instances", new=pcie_instances): 
        pcie_inst.check_configuration()

   
def test_check_configuration_invalid_pcie_gen(ofs_config, pcie_config, tmpdir):
    num_pfs = random.randrange(1,8)
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), mock.patch.object(pcie_inst, "pcie_gen", new=1): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

def test_check_configuration_invalid_pcie_instances(ofs_config, pcie_config, tmpdir):
    num_pfs = random.randrange(1,8)
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), mock.patch.object(pcie_inst, "pcie_gen", new="4"): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

def test_check_configuration_invalid_pcie_instances_enabled(ofs_config, pcie_config, tmpdir):
    num_pfs = random.randrange(1,8)
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), \
        mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), \
            mock.patch.object(pcie_inst, "pcie_gen", new="4"), \
                mock.patch.object(pcie_inst, "pcie_instances", new=2), \
                    mock.patch.object(pcie_inst, "pcie_instances_enabled", new=4): 
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            pcie_inst.check_configuration()

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

def test_process_configuration_with_preset_option(ofs_config, pcie_config, tmpdir):
    pcie_config["settings"]["preset"] = "sample_pcie_preset"
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
   
    pcie_inst.process_configuration()

    assert not pcie_inst.all_pfs
    assert not pcie_inst.pf_vf_count
    assert not pcie_inst.ip_component_params

def test_process_configuration_with_p_clk(ofs_config, pcie_config, tmpdir):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    rand_freq = random.randrange(256,2048)
    with mock.patch.object(pcie_inst, 'p_clk', new=rand_freq):
        pcie_inst.process_configuration()

        assert pcie_inst.ip_component_params["axi_st_clk_freq_user_hwtcl"] == f"{rand_freq}MHz"

def test_process_configuration_without_p_clk(ofs_config, pcie_config, tmpdir):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    
    pcie_inst.process_configuration()
    assert pcie_inst.ip_component_params["axi_st_clk_freq_user_hwtcl"] == "400MHz"


@pytest.mark.parametrize(
        'num_vfs, expected',
        [
            ([0, 0]),
            ([random.randrange(1,50), 1]),
        ]
)
def test_process_configuration_with_num_vfs(ofs_config, pcie_config, tmpdir, num_vfs, expected):
    pcie_config['pf0']['num_vfs'] = num_vfs
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    pcie_inst.process_configuration()

    assert pcie_inst.ip_component_params["core16_enable_sriov_hwtcl"] == expected

@pytest.mark.parametrize(
        'pcie_gen, pcie_instances',
        [
            (["4",random.randrange(1, 10)]),
            (["5",random.randrange(1, 10)]),
        ]
)
def test_process_configuration_valid_pcie_gen_num_instance(ofs_config, pcie_config, tmpdir, pcie_gen, pcie_instances):
    num_pfs = random.randrange(1,8)
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    mocked_pf_vf_count = {f"pf{n}":n for n in range(num_pfs)}
    with mock.patch.object(pcie_inst, "num_pfs", new=num_pfs), mock.patch.object(pcie_inst, "pf_vf_count", new=mocked_pf_vf_count), mock.patch.object(pcie_inst, "pcie_gen", new=pcie_gen), mock.patch.object(pcie_inst, "pcie_instances", new=pcie_instances): 
        pcie_inst.process_configuration()
    
    assert pcie_inst.ip_component_params['top_topology_hwtcl'] == f"Gen{pcie_gen} {pcie_instances}x16"

@pytest.mark.parametrize(
        'pasid_cap_enable, expected',
        [
            (["0", None]),
            (["False", None]),
            (["1", 20]), 
            (["True", 20]),
        ]
)
def test_override_pf_param_from_ofss_with_pasid_cap_enable(ofs_config, pcie_config, tmpdir, pasid_cap_enable, expected):
    pcie_config['pf0']['pasid_cap_enable'] = pasid_cap_enable
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    param = "AUTO_pasid_cap_max_pasid_width"
   
    result = pcie_inst.override_pf_param_from_ofss('pf0', param)
    
    assert result == expected


@pytest.mark.parametrize(
        'param, , param_val, expected',
        [
            (["bar0_address_width", None, None]),
            (["bar0_address_width", 64, 64]),
        ]
)
def test_override_pf_param_from_ofss_without_pasid_cap_enable(ofs_config, pcie_config, tmpdir, param, param_val, expected):
    pcie_config['pf0'][param] = param_val
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    
   
    result = pcie_inst.override_pf_param_from_ofss('pf0', param)
    
    assert result == expected



def test_override_pf_param_from_ofss_with_known_param(ofs_config, pcie_config, tmpdir, sample_param_dict):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    pf = f'pf{random.randrange(8)}'
    with mock.patch.object(pcie_inst, 'override_pf_param_from_ofss', return_value=0xF0CACC1A):
        pcie_inst.set_func_params(sample_param_dict, pf)

    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_type0_vendor_id_hwtcl"] == 0xF0CACC1A
    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_type0_vendor_id_user_hwtcl"] == 0xF0CACC1A
    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_msix_table_offset_hwtcl"] != 0xF0CACC1A

def test_process_configuration_second_link_core16(ofs_config, pcie_config, tmpdir, pcie_core_params):
    pcie_core_params["core8_abcd"] = "abcd" 
    pcie_core_params["core8_efgh"] = "egfh"
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)

    with mock.patch.object(pcie_inst, "get_ip_settings", return_value=None), \
        mock.patch.object(pcie_inst, "process_pfs", return_value=None), \
        mock.patch.object(pcie_inst, 'ip_component_params', new=pcie_core_params), \
            mock.patch.object(pcie_inst, "pcie_instances", new=2), \
                mock.patch.object(pcie_inst, "pcie_instances_enabled", new=2):
        
        pcie_inst.process_configuration()
    
        assert len(pcie_inst.ip_component_params) == 12 #original length + 4 (where the core16 params has core8 ones now) + 2
        assert pcie_inst.ip_component_params['core8_xxx'] == 'x'
        assert pcie_inst.ip_component_params['core8_yyyy'] == 'y'
        assert pcie_inst.ip_component_params['core8_z'] == 5
        assert pcie_inst.ip_component_params['core8_1234'] == 1234
        assert pcie_inst.ip_component_params['core8_abcd'] == 'abcd'
        assert pcie_inst.ip_component_params['core8_efgh'] == 'egfh'

def test_process_configuration_second_link_with_existing_core8(ofs_config, pcie_config, tmpdir, pcie_core_params):
    pcie_core_params["core8_abcd"] = "abcd" 
    pcie_core_params["core8_efgh"] = "egfh"
    pcie_core_params['core16_abcd'] = "a16b16c16"
    pcie_core_params['core16_efgh'] = "e16f16h16"
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)

    with mock.patch.object(pcie_inst, "get_ip_settings", return_value=None), \
        mock.patch.object(pcie_inst, "process_pfs", return_value=None), \
        mock.patch.object(pcie_inst, 'ip_component_params', new=pcie_core_params), \
            mock.patch.object(pcie_inst, "pcie_instances", new=2), \
                mock.patch.object(pcie_inst, "pcie_instances_enabled", new=2):
       
        pcie_inst.process_configuration()
    
        assert len(pcie_inst.ip_component_params) == 14 #original length + 4 (where the core16 params has core8 ones now)
        assert pcie_inst.ip_component_params['core8_xxx'] == 'x'
        assert pcie_inst.ip_component_params['core8_yyyy'] == 'y'
        assert pcie_inst.ip_component_params['core8_z'] == 5
        assert pcie_inst.ip_component_params['core8_1234'] == 1234
        assert pcie_inst.ip_component_params['core8_abcd'] == 'abcd'
        assert pcie_inst.ip_component_params['core8_efgh'] == 'egfh'


@pytest.mark.parametrize(
        'pf, vf_count',
        [
            (["pf1",random.randrange(1, 200)]),
            (["pf2",random.randrange(1, 200)]),
            (["pf3",random.randrange(1, 200)]),
            (["pf4",random.randrange(1, 200)]),
            (["pf5",random.randrange(1, 200)]),
        ]
)
def test_process_pf(ofs_config, pcie_config, tmpdir, pf, vf_count):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    
    with mock.patch.object(pcie_inst, "set_func_params", return_value=None), mock.patch.object(pcie_inst, "process_vfs", return_value=None), mock.patch.dict(pcie_inst.pf_vf_count, {pf: vf_count}):
        pcie_inst.process_pfs(pf)
    
    assert pcie_inst.ip_component_params[f"core16_{pf}_vf_count_hwtcl"] == vf_count

@pytest.mark.parametrize(
        'pf, vf_count, num_vfs',
        [
            (["pf1",random.randrange(1, 20), random.randrange(1, 20)]),
            (["pf2",random.randrange(1, 20), random.randrange(1, 20)]),
            (["pf3",random.randrange(1, 20), random.randrange(1, 20)]),
            (["pf4",random.randrange(1, 20), random.randrange(1, 20)]),
            (["pf5",random.randrange(1, 20), random.randrange(1, 20)]),
        ]
)
def test_process_vf(ofs_config, pcie_config, tmpdir, pf, vf_count, num_vfs):
    pcie_config[pf] = {'num_vfs':vf_count}
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    
    with mock.patch.object(pcie_inst, "num_vfs", num_vfs):
        print(pcie_inst.pf_vf_count)
        pcie_inst.process_vfs(pf)
    
        assert pcie_inst.pf_vf_count[pf] == vf_count
        assert pcie_inst.num_vfs == vf_count + num_vfs
        assert pcie_inst.ip_component_params[f"core16_exvf_msix_tablesize_{pf}"] ==  6
        assert pcie_inst.ip_component_params[f"core16_exvf_msixtable_offset_{pf}"] == 1536
        assert pcie_inst.ip_component_params[f"core16_exvf_msixtable_bir_{pf}"] == 4
        assert pcie_inst.ip_component_params[f"core16_exvf_msixpba_bir_{pf}"] ==  4
        assert pcie_inst.ip_component_params[f"core16_exvf_msixpba_offset_{pf}"] == 1550

def test_process_pf_with_no_vfs(ofs_config, pcie_config, tmpdir):
    pf = f'pf{random.randrange(8)}'
    pcie_config[pf] = {'num_vfs':0}
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    pcie_inst.process_pfs(pf)
    assert pcie_inst.pf_vf_count[pf] == 0
    assert pcie_inst.ip_component_params[f"core16_exvf_msix_tablesize_{pf}"] ==  0
    assert pcie_inst.ip_component_params[f"core16_exvf_msixtable_offset_{pf}"] == 0
    assert pcie_inst.ip_component_params[f"core16_exvf_msixtable_bir_{pf}"] == 0
    assert pcie_inst.ip_component_params[f"core16_exvf_msixpba_bir_{pf}"] ==  0
    assert pcie_inst.ip_component_params[f"core16_exvf_msixpba_offset_{pf}"] == 0

def test_set_func_params_with_no_override(ofs_config, pcie_config, tmpdir, sample_param_dict):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    pf = f'pf{random.randrange(8)}'
    with mock.patch.object(pcie_inst, 'override_pf_param_from_ofss', return_value=None):
        pcie_inst.set_func_params(sample_param_dict, pf)

    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_type0_vendor_id_hwtcl"] == 0xFEEDBEEF
    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_type0_vendor_id_user_hwtcl"] == "0xDEADBEEF"
    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_msix_table_offset_hwtcl"] == 1337

def test_set_func_params_with_override(ofs_config, pcie_config, tmpdir, sample_param_dict):
    pcie_inst = PCIe(ofs_config, pcie_config, tmpdir)
    pf = f'pf{random.randrange(8)}'
    with mock.patch.object(pcie_inst, 'override_pf_param_from_ofss', return_value=0xF0CACC1A):
        pcie_inst.set_func_params(sample_param_dict, pf)

    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_type0_vendor_id_hwtcl"] == 0xF0CACC1A
    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_type0_vendor_id_user_hwtcl"] == 0xF0CACC1A
    assert pcie_inst.ip_component_params[f"core16_{pf}_pci_msix_table_offset_hwtcl"] != 0xF0CACC1A

   

