# cvp-spt
Environment variables
--

* Set IMAGE_SIZE_MB env variable to have specific image size in cvp-spt/test_glance.py tests

* [test_vm2vm] allowable next overrides:
flavor_name='spt-test'  to set flavor name
flavor_ram=1536         to define RAM allocation for specific flavor
flavor_vcpus=1          to define a count of vCPU for flavor
flavor_disk=5           to define a count of disks on flavor
