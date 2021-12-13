# mos-spt

Requirements
--
 At least Python 3.6 is required for the tests.

Installation
--
```
cd mos-spt/
virtualenv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Configuration
--
 Open _global_config.yaml_ file to override the settings, or export the 
 environment variables.

Settings
--
 The following options can be set in _global_config.yaml_ file, or by exporting
 the environment variables.

* **test_glance** allows next overrides:

| Environment Variable | Default | Description |
| --- | --- | --- |
| IMAGE_SIZE_MB | 2000 | Specific image size (in MB) to upload/download at Glance |

* **test_vm2vm** allows next overrides:

| Environment Variable | Default | Description |
| --- | --- | --- |
| flavor_name | spt-test | Flavor name |
| flavor_ram | 1536 | To define RAM allocation for specific flavor, MB |
| flavor_vcpus | 1 | To define a count of vCPU for flavor |
| flavor_disk | 5 | To define a count of disks on flavor, GB |
| image_name | Ubuntu-18.04 | Cloud Ubuntu image to create VMs |
| CMP_HOSTS | "" | Pair of compute hosts to create VMs at different hosts. By default, some random pair from nova compute list will be selected. To set some pair, set _CMP_HOSTS: ["cmp001", "cmp002"]_ in _global_config.yaml_ file, or export CMP_HOSTS="cmp001,cmp002". | 
| skipped_nodes | "" | Skip some compute hosts, so they are not selected at CMP_HOSTS pair. To set some nodes to skip, set _skipped_nodes: ["cmp003"]_ in _global_config.yaml_ file, or export skipped_nodes="cmp003".|
| nova_timeout | 300 | Timeout to VM to be ACTIVE, seconds. |
| external_network | public | External network name to allocate the Floating IPs |
| ssh_timeout | 500 | Timeout to VM to be reachable via SSH, seconds. |
| iperf_prep_string | "sudo /bin/bash -c 'echo \"91.189.88.161        archive.ubuntu.com\" >> /etc/hosts'" | Preparation string to set ubuntu repository host in /etc/hosts of VMs |
| internet_at_vms | 'true' | In case True, the Internet is present at VMs, and the tests are able to install iperf3 by _apt update; apt install iperf3_. In case VMs have no Internet, set 'false' and the iperf3 will be installed from offline *.deb packages. |
| iperf_deb_package_dir_path | /artifacts/mos-spt/ | Path to the local directory where the iperf3 *.deb packages are present. You need to download/copy them there manually beforehand. |
| iperf_time | 60 | iperf3 -t option value: time in seconds to transmit for (iperf -t option). |

 In case _internet_at_vms=false_, download the iperf3 packages from:
```
wget https://iperf.fr/download/ubuntu/libiperf0_3.1.3-1_amd64.deb 
wget https://iperf.fr/download/ubuntu/iperf3_3.1.3-1_amd64.deb 
```
 and place both of them to the path equal to _iperf_deb_package_dir_path_.

Executing tests
--
 Run tests:
```
pytest -sv --tb=short tests/
```
 In case the test is skipped and you want to know the reason, use python -rs option:
```
pytest -rs --tb=short tests/
```

Enable logging
--
 In case something went wrong, use logging of the tests, set “log_cli=true” 
 in pytest.ini and rerun tests. By default, the log level is INFO 
 _log_cli_level=info_. In case you want to go deeper for the API requests 
 (with URIs, payloads, etc), set _cli_level=debug_.
