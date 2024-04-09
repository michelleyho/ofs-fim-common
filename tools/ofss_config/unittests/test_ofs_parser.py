import pytest
import ofs_parser
import argparse
import os
import sys
import logging
import collections
from unittest import mock
from contextlib import nullcontext as does_not_raise

def test_print_ip_config(ofss_data, caplog):
    with caplog.at_level(logging.INFO):
        ofs_parser.print_ip_config(ofss_data)
    
    #print(caplog.records[-1])
    all_logs = [rec.message.replace("\t", " ") for rec in caplog.records]
    print(all_logs)
    
    expected = [' DEFAULT:', '  sampledefault : 123', ' ip:', '  sampleip : ip_123', '  sampledefault : 123', ' include:', '  some/path/a : n/a', '  some/path/b : n/a', '  "$sample_rootdir"/c : n/a', '  sampledefault : 123', ' key_a:', '  answer : yes', '  sampledefault : 123', ' key_b:', '  answer : yes', '  sampledefault : 123', ' key_c:', '  answer : yes', '  sampledefault : 123']
    assert "key_a" in caplog.text
    assert expected == all_logs

def test_process_input_arguments_ofss_flag(capsys):
    with mock.patch.object(sys, 'argv', ['_', '--ofss', 'hads', 'abc']):
        p_args = ofs_parser.process_input_arguments()
        #captured = capsys.readouterr()
        #assert captured.out == "Hello hads\n"
        assert p_args.ofss == ["hads", "abc"]

@pytest.mark.skip
@pytest.mark.parametrize('x', [1])
@mock.patch.object(sys, 'argv', ['_', '--ini', 'hads', 'abc']) 
def test_process_input_arguments_ini(capsys, x):
    p_args = ofs_parser.process_input_arguments()
    assert p_args.ofss == ["hads", "abc"]

@pytest.mark.parametrize('val, expected', [(['adaa'], ['adaa']), (['gbb'], ['gbb']), (["abc", "def"], ["abc", "def"])])
def test_process_input_arguments_ini_flag(capsys, val, expected):
    with mock.patch.object(sys, 'argv', ['_', '--ofss', *val]):
        print(sys.argv)
        p_args = ofs_parser.process_input_arguments()
        #captured = capsys.readouterr()
        #assert captured.out == "Hello hads\n"
        assert p_args.ofss == expected  

def test_process_config_sections(ofss_data):
    result = ofs_parser.process_config_sections(ofss_data)

    assert "key_a" in result
    assert "key_b" in result
    assert "key_c" in result
    assert "ip" not in result
    assert "DEFAULT" not in result
    assert "include" not in result

def test_process_config_includes(ofss_data, monkeypatch_env_rootdir):
    sample_queue = list()
    sample_queue.append("path/to/A")
    sample_queue.append("path/to/B")

    ofs_parser.process_config_includes(sample_queue, ofss_data)
    assert len(sample_queue) == 6
    assert "some/path/a" in sample_queue
    assert "some/path/b" in sample_queue
    assert '$sample_path/c' not in sample_queue
    assert 'imaginary/path/c' in sample_queue

def test_process_config_without_includes(ofss_data):
    del ofss_data["include"]

    sample_queue = list()
    sample_queue.append("path/to/A")
    sample_queue.append("path/to/B")

    ofs_parser.process_config_includes(sample_queue, ofss_data)
    assert len(sample_queue) == 2
    assert sample_queue == ["path/to/A", "path/to/B"]

def test_check_ofs_config(ofss_project):
    ofss_project["ofs"][0]["settings"]["family"] = "agilex"
    ofs_parser.check_ofs_config(ofss_project["ofs"][0]["settings"])
    
@pytest.mark.parametrize('missing_info', ['platform', 'family', 'part', 'device_id'])
def test_check_ofs_config_with_missing_project_info(ofss_project, missing_info):
    del ofss_project['ofs'][0]['settings'][missing_info]
    
    with pytest.raises(SystemExit) as pytest_wrapped_e:
            ofs_parser.check_ofs_config(ofss_project["ofs"][0]["settings"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


def test_check_ofs_config_with_wrong_family(ofss_project):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
          ofs_parser.check_ofs_config(ofss_project["ofs"][0]["settings"])
    
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

#@pytest.mark.parametrize('ip_input, expectation',[('pcie', does_not_raise())])
def test_check_num_ip_configs_with_pcie(ofss_project):
#def test_check_num_configs_pcie(ofss_project, ip_input, expectation):
    sample_data = ofss_project.copy()
    #with pytest.raises(SystemExit) as pytest_wrapped_e:
    #    ofs_parser.check_num_ip_configs("pcie", sample_data["pcie"]) 
    #    # if ip is pcie, and it has more than one config, function should return with no issue
    #    sys.exit()
    #with expectation as e:
    #     ofs_parser.check_num_ip_configs(ip_input, sample_data['pcie'])
    ofs_parser.check_num_ip_configs('pcie', sample_data['pcie'])

@pytest.mark.parametrize('repeated_info_to_check', ['hssi', 'mem'])
def test_check_num_ip_configs_with_ip_greater_than_one(ofss_project, repeated_info_to_check, caplog):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
            with caplog.at_level(logging.INFO):
                ofs_parser.check_num_ip_configs(repeated_info_to_check, ofss_project[repeated_info_to_check])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
   
    all_logs = [rec.message for rec in caplog.records]
   
    assert f"!!Error!! {repeated_info_to_check} should only have 1 set of configuration" in all_logs

def test_check_num_configs_with_exactly_one_ip(ofss_project):
    ofs_parser.check_num_ip_configs('sim_mem', ofss_project['sim_mem'])
    
def test_check_configurations(mocker, ofss_project):
    method1_mock = mocker.patch("ofs_parser.check_ofs_config")
    result = ofs_parser.check_configurations(ofss_project)
    method1_mock.assert_called_once()
    #assert  method1_mock.called

def test_check_configurations_without_ofs_param(ofss_project):
    del ofss_project["ofs"]

    with pytest.raises(SystemExit) as pytest_wrapped_e:
            ofs_parser.check_configurations(ofss_project)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

@pytest.mark.skip
def test_process_ofss_configs_one_ofss(monkeypatch):
    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    
    ofss_list = [os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", "n6001.ofss")]
    result = ofs_parser.process_ofss_configs(ofss_list)

    expected_keys = ['ofs', 'pcie', 'memory', 'iopll']
    for e_key in expected_keys:
         assert e_key in result.keys()
    expected_pcie_keys = ['pf0', 'pf1', 'pf2', 'pf3', 'pf4']
    for e_pcie_key in expected_pcie_keys:
         assert e_pcie_key in result['pcie'][0].keys()


@pytest.mark.parametrize('test_file1, test_file2',
                          [(["n6001.ofss", "hssi/hssi_8x25.ofss"]), 
                           (["n6001.ofss,", "hssi/hssi_8x25.ofss"]),
                           (["n6001.ofss, ", "hssi/hssi_8x25.ofss "]),
                           ]
                          )
def test_process_ofss_configs_two_ofss_space_comma_separated(monkeypatch, test_file1, test_file2):
    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    
    file_one = os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", test_file1)
    file_two = os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", test_file2)
                    
    ofss_list = [f"{file_one}", f"{file_two}"]
    result = ofs_parser.process_ofss_configs(ofss_list)

    expected_keys = ['ofs', 'pcie', 'memory', 'iopll', 'hssi']
    for e_key in expected_keys:
         assert e_key in result.keys()
    expected_pcie_keys = ['pf0', 'pf1', 'pf2', 'pf3', 'pf4']
    for e_pcie_key in expected_pcie_keys:
         assert e_pcie_key in result['pcie'][0].keys()

def test_process_ofss_configs_repeated_files(monkeypatch):
    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    
    file_one = os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", "n6001.ofss")
    file_two = os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", "hssi/hssi_8x25.ofss")
    file_three = os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", "pcie/pcie_host.ofss") 

    ofss_list = [file_one, file_two, file_three]
    result = ofs_parser.process_ofss_configs(ofss_list)

    expected_keys = ['ofs', 'pcie', 'memory', 'iopll', 'hssi']
    for e_key in expected_keys:
         assert e_key in result.keys()
    expected_pcie_keys = ['pf0', 'pf1', 'pf2', 'pf3', 'pf4']
    for e_pcie_key in expected_pcie_keys:
         assert e_pcie_key in result['pcie'][0].keys()

def test_process_ofss_configs_nonexistent_files(monkeypatch):

    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    file_one = os.path.join(os.getenv("OFS_ROOTDIR"),"tools", "ofss_config", "made_up.ofss")
    
    ofss_list = [file_one]

    with pytest.raises(FileNotFoundError) as pytest_wrapped_e:
          ofs_parser.process_ofss_configs(ofss_list)
   
    assert pytest_wrapped_e.type == FileNotFoundError
    assert str(pytest_wrapped_e.value) == f"{file_one} not found"

#@mock.patch('argparse.ArgumentParser.parse_args',
 #           return_value=argparse.Namespace(ofss=["/Users/michimochi/Documents/github_repos/OFS/ofs-agx7-pcie-attach/tools/ofss_config/n6001.ofss", "/Users/michimochi/Documents/github_repos/OFS/ofs-agx7-pcie-attach/tools/ofss_config/hssi/hssi_8x25.ofss"]))
@mock.patch.object(sys, 'argv', ['_', '--ini', '/Users/michimochi/Documents/github_repos/OFS/ofs-agx7-pcie-attach/tools/ofss_config/n6001.ofss']) 
def test_main(mocker, monkeypatch):
    monkeypatch.setenv("OFS_ROOTDIR", os.path.realpath("../../../"))
    ofs_parser.main()

