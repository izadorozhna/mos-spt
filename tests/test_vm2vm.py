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
    result_table = Texttable()
    try:
        zone1 = [service.zone for service in openstack_clients.compute.services.list() if service.host == pair[0]]
        zone2 = [service.zone for service in openstack_clients.compute.services.list() if service.host == pair[1]]
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
        vms.extend([vm1,vm2,vm3,vm4])
        fips = []
        time.sleep(5)
        for i in range(4):
            fip = openstack_clients.compute.floating_ips.create(os_resources['ext_net']['name'])
            fips.append(fip.id)
            status = openstack_clients.compute.servers.get(vms[i]).status
            if status != 'ACTIVE':
                print("VM #{0} {1} is not ready. Status {2}".format(i,vms[i].id,status))
                time.sleep(timeout)
                status = openstack_clients.compute.servers.get(vms[i]).status
            if status != 'ACTIVE':
                raise Exception('VM is not ready')
            vms[i].add_floating_ip(fip)
            private_address = vms[i].addresses[list(vms[i].addresses.keys())[0]][0]['addr']
            time.sleep(5)
            try:
                ssh.prepare_iperf(fip.ip,private_key=os_resources['keypair'].private_key)
            except Exception as e:
                print(e)
                print("ssh.prepare_iperf was not successful, retry after {} sec".format(timeout))
                time.sleep(timeout)
                ssh.prepare_iperf(fip.ip,private_key=os_resources['keypair'].private_key)
            vm_info.append({'vm': vms[i], 'fip': fip.ip, 'private_address': private_address})

        transport1 = ssh.SSHTransport(vm_info[0]['fip'], 'ubuntu', password='dd', private_key=os_resources['keypair'].private_key)
        table_rows = []
        table_rows.append(['Test Case', 'Host 1', 'Host 2', 'Result'])

        result1 = transport1.exec_command('iperf -c {} -t 60 | tail -n 1'.format(vm_info[1]['private_address']))
        res1 = b" ".join(result1.split()[-2::])
        table_rows.append(['VM to VM in same tenant on same node via Private IP, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[0]),
                                "{}".format(res1)])

        result2 = transport1.exec_command('iperf -c {} -t 60 | tail -n 1'.format(vm_info[2]['private_address']))
        res2 = b" ".join(result2.split()[-2::])
        table_rows.append(['VM to VM in same tenant on different HW nodes via Private IP, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res2)])

        result3 = transport1.exec_command('iperf -c {} -P 10 -t 60 | tail -n 1'.format(vm_info[2]['private_address']))
        res3 = b" ".join(result3.split()[-2::])
        table_rows.append(['VM to VM in same tenant on different HW nodes via Private IP, 10 threads',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res3)])

        result4 = transport1.exec_command('iperf -c {} -t 60 | tail -n 1'.format(vm_info[2]['fip']))
        res4 = b" ".join(result4.split()[-2::])
        table_rows.append(['VM to VM in same tenant via Floating IP and VMs are on different nodes, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res4)])

        result5 = transport1.exec_command('iperf -c {} -t 60 | tail -n 1'.format(vm_info[3]['private_address']))
        res5 = b" ".join(result5.split()[-2::])
        table_rows.append(['VM to VM in same tenant, different HW nodes and each VM is connected to separate network which are connected using Router via Private IP, 1 thread',
                                "{}".format(pair[0]),
                                "{}".format(pair[1]),
                                "{}".format(res5)])

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
        for vm in vms:
            openstack_clients.compute.servers.delete(vm)
        for fip in fips:
            openstack_clients.compute.floating_ips.delete(fip)
        pytest.fail("Something went wrong")
