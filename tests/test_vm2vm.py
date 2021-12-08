import os
import random
import time

import pytest
from texttable import Texttable

import utils
from utils import os_client
from utils import ssh


def test_vm2vm(openstack_clients, pair, os_resources, record_property):
    os_actions = os_client.OSCliActions(openstack_clients)
    config = utils.get_configuration()
    timeout = int(config.get('nova_timeout', 30))
    iperf_time = int(config.get('iperf_time', 60))
    private_key = os_resources['keypair'].private_key
    ssh_timeout = int(config.get('ssh_timeout', 500))
    result_table = Texttable()

    try:
        zone1 = [service.zone for service in
                 openstack_clients.compute.services.list() if
                 service.host == pair[0]]
        zone2 = [service.zone for service in
                 openstack_clients.compute.services.list()
                 if service.host == pair[1]]
        vm1 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(zone1[0],pair[0]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm2 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(zone1[0],pair[0]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm3 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net1'],
                                             '{0}:{1}'.format(zone2[0],pair[1]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm4 = os_actions.create_basic_server(os_resources['image_id'],
                                             os_resources['flavor_id'],
                                             os_resources['net2'],
                                             '{0}:{1}'.format(zone2[0],pair[1]),
                                             [os_resources['sec_group'].name],
                                             os_resources['keypair'].name)

        vm_info = []
        vms = []
        vms.extend([vm1, vm2, vm3, vm4])
        fips = []
        time.sleep(5)

        # Associate FIPs and check VMs are Active
        for i in range(4):
            fip = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
            fips.append(fip.id)
            os_actions.check_vm_is_active(vms[i].id, timeout=timeout)
            vms[i].add_floating_ip(fip)
            private_address = vms[i].addresses[list(vms[i].addresses.keys())[0]][0]['addr']
            vm_info.append({'vm': vms[i], 'fip': fip.ip,
                            'private_address': private_address})
        # Check VMs are reachable and prepare iperf
        transport1 = ssh.SSHTransport(vm_info[0]['fip'], 'ubuntu',
                                      password='dd', private_key=private_key)
        for i in range(4):
            if transport1.check_vm_is_reachable_ssh(
                    floating_ip=vm_info[i]['fip'], timeout=ssh_timeout):
                print("\nizadorozhna: VM - do prepare iperf")
                ssh.prepare_iperf(vm_info[i]['fip'], private_key=private_key)
        # Prepare the result table and run iperf
        table_rows = []
        table_rows.append(['Test Case', 'Host 1', 'Host 2', 'Result'])

        result1 = transport1.exec_command('iperf -c {} -t {} | tail -n 1'.format(vm_info[1]['private_address'], iperf_time))
        res1 = b" ".join(result1.split()[-2::])
        table_rows.append(['VM to VM in same tenant on same node via Private IP, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[0]),
                                "{}".format(res1.decode('utf-8'))])

        result2 = transport1.exec_command('iperf -c {} -t {} | tail -n 1'.format(vm_info[2]['private_address'], iperf_time))
        res2 = b" ".join(result2.split()[-2::])
        table_rows.append(['VM to VM in same tenant on different HW nodes via Private IP, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res2.decode('utf-8'))])

        result3 = transport1.exec_command('iperf -c {} -P 10 -t {} | tail -n 1'.format(vm_info[2]['private_address'], iperf_time))
        res3 = b" ".join(result3.split()[-2::])
        table_rows.append(['VM to VM in same tenant on different HW nodes via Private IP, 10 threads',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res3.decode('utf-8'))])

        result4 = transport1.exec_command('iperf -c {} -t {} | tail -n 1'.format(vm_info[2]['fip'], iperf_time))
        res4 = b" ".join(result4.split()[-2::])
        table_rows.append(['VM to VM in same tenant via Floating IP and VMs are on different nodes, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res4.decode('utf-8'))])

        result5 = transport1.exec_command('iperf -c {} -t {} | tail -n 1'.format(vm_info[3]['private_address'], iperf_time))
        res5 = b" ".join(result5.split()[-2::])
        table_rows.append(['VM to VM in same tenant, different HW nodes and each VM is connected to separate network which are connected using Router via Private IP, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res5.decode('utf-8'))])

        result_table.add_rows(table_rows)
        print(result_table.draw())

        print("Removing VMs...")
        for vm in vms:
            openstack_clients.compute.servers.delete(vm)
        print("Removing FIPs...")
        for fip in fips:
            openstack_clients.compute.floating_ips.delete(fip)
    except Exception as e:
        print(e)
        print("Something went wrong")
        if 'vms' in locals():
            for vm in vms:
                openstack_clients.compute.servers.delete(vm)
            if 'fips' in locals():
                for fip in fips:
                    openstack_clients.compute.floating_ips.delete(fip)
        else:
            print("Skipping cleaning, VMs were not created")
        pytest.fail("Something went wrong")
