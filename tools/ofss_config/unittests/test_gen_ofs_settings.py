import pytest
import gen_ofs_settings
from hssi_ip import HSSI as HSSI
from iopll_ip import IOPLL as IOPLL
from memory_ip import Memory as Memory, SimMemory as SimMemory
from pcie_ip import PCIe as PCIe
import argparse
import os
import sys
import logging
import collections
from unittest import mock
from contextlib import nullcontext as does_not_raise

@pytest.mark.parametrize('flag_value', [(['adaa']), (['gbb']), (["abc", "def"])])
def test_process_input_arguments_ini_flag(capsys, flag_value):
    with mock.patch.object(sys, 'argv', ['_', '--ini', *flag_value]):
        p_args = gen_ofs_settings.process_input_arguments()
        assert p_args.ofss == flag_value


@pytest.mark.parametrize('flag_value', [(['adaa']), (['gbb']), (["abc", "def"])])
def test_process_input_arguments_ini_flag(capsys, flag_value):
    with mock.patch.object(sys, 'argv', ['_', '--ofss', *flag_value]):
        p_args = gen_ofs_settings.process_input_arguments()
        assert p_args.ofss == flag_value

def test_process_input_arguments_platform_flag(capsys):
    with mock.patch.object(sys, 'argv', ['_', '--ofss', 'abc', '--platform', 'def']):
        p_args = gen_ofs_settings.process_input_arguments()
        assert p_args.ofss == ['abc']
        assert p_args.platform == 'def'

def test_process_input_arguments_target_flag(capsys):
    with mock.patch.object(sys, 'argv', ['_', '--ofss', 'abc', '--target', 'some/dir/path']):
        p_args = gen_ofs_settings.process_input_arguments()
        assert p_args.target == 'some/dir/path'

def test_process_input_arguments_debug_flag(capsys):
    with mock.patch.object(sys, 'argv', ['_', '--ofss', 'abc', '--debug']):
        p_args = gen_ofs_settings.process_input_arguments()
        assert p_args.debug == True

def test_instantiate_ips_with_all_ip_types(sample_ofs_ip_configurations, tmpdir):
    result = gen_ofs_settings.instantiate_ips(sample_ofs_ip_configurations, tmpdir)
    assert len(result) == 5
    for ip in result:
        print(ip)
        assert isinstance(ip, (IOPLL, PCIe, HSSI, SimMemory, Memory)) 
    assert "p_clk" in sample_ofs_ip_configurations["ofs"][0]["settings"]

@pytest.mark.parametrize(
        "single_ip, expected_ip_class, expected_len",
        [
            ("pcie", (PCIe), 1),
            ("hssi", (HSSI), 1),
            ("iopll", (IOPLL), 1),
            ("memory", (Memory, SimMemory), 2)
        ],
)
def test_instantiate_ips_with_one_ip_only(sample_ofs_ip_configurations, single_ip, expected_ip_class, expected_len, tmpdir):
    ips_to_keep = ["ofs", single_ip]
    data = sample_ofs_ip_configurations.copy()
    all_ips = list(data.keys())
    for ip in all_ips:
        if ip not in ips_to_keep:
            del data[ip]
  
    result = gen_ofs_settings.instantiate_ips(data, tmpdir)
 
    assert len(result) == expected_len
    for ip in result:
        assert isinstance(ip, (expected_ip_class))

def test_instantiate_ips_with_no_iopll(sample_ofs_ip_configurations, tmpdir):
    data = sample_ofs_ip_configurations.copy()
    all_ips = list(data.keys())
    if "iopll" in data:
        del data["iopll"]
    
    result = gen_ofs_settings.instantiate_ips(data, tmpdir)
    assert len(result) == 4
    assert "p_clk" not in data["ofs"][0]["settings"]


@mock.patch.object(sys, 'argv', ['_', '--ini', '/Users/michimochi/Documents/github_repos/OFS/ofs-agx7-pcie-attach/tools/ofss_config/n6001.ofss']) 
def test_gen_ofs_settings_main(monkeypatch, tmpdir):
    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    gen_ofs_settings.main()
    assert not os.path.exists("ip_deploy_cmds.log")

@mock.patch.object(sys, 'argv', ['_', '--ini', '/Users/michimochi/Documents/github_repos/OFS/ofs-agx7-pcie-attach/tools/ofss_config/n6001.ofss', '--debug']) 
def test_gen_ofs_settings_main_with_debug(monkeypatch, tmpdir):
    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    gen_ofs_settings.main()
    assert os.path.exists("ip_deploy_cmds.log")
    os.remove("ip_deploy_cmds.log")
    
    

