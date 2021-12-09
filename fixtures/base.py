import os
import pytest
import utils
import random
import time
import logging

from utils import os_client


logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def openstack_clients():
    return os_client.OfficialClientManager(
        username=os.environ['OS_USERNAME'],
        password=os.environ['OS_PASSWORD'],
        tenant_name=os.environ['OS_PROJECT_NAME'],
        auth_url=os.environ['OS_AUTH_URL'],
        cert=False,
        domain=os.environ['OS_PROJECT_DOMAIN_NAME'],
        )


nodes = utils.get_pairs()


@pytest.fixture(scope='session', params=nodes.values(), ids=nodes.keys())
def pair(request):
    return request.param


@pytest.fixture(scope='session')
def os_resources(openstack_clients):
    os_actions = os_client.OSCliActions(openstack_clients)
    os_resource = {}
    config = utils.get_configuration()
    image_name = config.get('image_name', 'Ubuntu-18.04')
    flavor_name = config.get('flavor_name', 'spt-test')
    flavor_ram = config.get('flavor_ram', 1536)
    flavor_vcpus = config.get('flavor_vcpus', 1)
    flavor_disk = config.get('flavor_disk', 3)

    os_images_list = [image.id for image in
                      openstack_clients.image.images.list(
                          filters={'name': image_name})]

    if os_images_list.__len__() == 0:
        pytest.skip("No images with name {}. This name can be redefined "
                    "with 'image_name' env var ".format(image_name))

    os_resource['image_id'] = str(os_images_list[0])

    os_resource['flavor_id'] = [flavor.id for flavor in
                                openstack_clients.compute.flavors.list()
                                if flavor.name == flavor_name]
    flavor_is_created = False
    if not os_resource['flavor_id']:
        os_resource['flavor_id'] = os_actions.create_flavor(
            flavor_name, flavor_ram, flavor_vcpus, flavor_disk).id
        flavor_is_created = True
    else:
        os_resource['flavor_id'] = str(os_resource['flavor_id'][0])

    os_resource['sec_group'] = os_actions.create_sec_group()
    os_resource['keypair'] = openstack_clients.compute.keypairs.create(
        '{}-{}'.format('spt-key', random.randrange(100, 999))
    )
    os_resource['net1'] = os_actions.create_network_resources()
    os_resource['ext_net'] = os_actions.get_external_network()
    adm_tenant = os_actions.get_admin_tenant()
    os_resource['router'] = os_actions.create_router(
        os_resource['ext_net'], adm_tenant.id)
    os_resource['net2'] = os_actions.create_network(adm_tenant.id)
    os_resource['subnet2'] = os_actions.create_subnet(
        os_resource['net2'], adm_tenant.id, '10.2.7.0/24')
    for subnet in openstack_clients.network.list_subnets()['subnets']:
        if subnet['network_id'] == os_resource['net1']['id']:
            os_resource['subnet1'] = subnet['id']

    openstack_clients.network.add_interface_router(
        os_resource['router']['id'],{'subnet_id': os_resource['subnet1']})
    openstack_clients.network.add_interface_router(
        os_resource['router']['id'],
        {'subnet_id': os_resource['subnet2']['id']})
    yield os_resource

    # cleanup created resources
    logger.info("Deleting routers, networks, SG, key pair, flavor...")
    openstack_clients.network.remove_interface_router(
        os_resource['router']['id'], {'subnet_id': os_resource['subnet1']})
    openstack_clients.network.remove_interface_router(
        os_resource['router']['id'],
        {'subnet_id': os_resource['subnet2']['id']})
    openstack_clients.network.remove_gateway_router(
        os_resource['router']['id'])
    time.sleep(5)
    openstack_clients.network.delete_router(os_resource['router']['id'])
    time.sleep(5)
    openstack_clients.network.delete_network(os_resource['net1']['id'])
    openstack_clients.network.delete_network(os_resource['net2']['id'])

    openstack_clients.compute.security_groups.delete(
        os_resource['sec_group'].id)
    openstack_clients.compute.keypairs.delete(os_resource['keypair'].name)
    if flavor_is_created:
        openstack_clients.compute.flavors.delete(os_resource['flavor_id'])
