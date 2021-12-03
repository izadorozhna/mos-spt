# cvp-spt
Environment variables
--

* Set IMAGE_SIZE_MB env variable to have specific image size in cvp-spt/test_glance.py tests

* [test_vm2vm] allowable next overrides:
flavor_name='spt-test'  to set flavor name
flavor_ram=1536         to define RAM allocation for specific flavor
flavor_vcpus=1          to define a count of vCPU for flavor
flavor_disk=5           to define a count of disks on flavor

* *cvp-spt.test_glance*   Error may happen while executing images.upload:
```python
CommunicationError: Error finding address for http://os-ctl-vip.<>.local:9292/v2/images/8bce33dd-9837-4646-b747-7f7f5ce01092/file:
Unable to establish connection to http://os-ctl-vip.<>.local:9292/v2/images/8bce33dd-9837-4646-b747-7f7f5ce01092/file: [Errno 32] Broken pipe
```
This may happen because of low disk space on ctl node or old cryptography package (will be fixed after upgrading to Python3)

