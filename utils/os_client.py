from cinderclient import client as cinder_client
from glanceclient import client as glance_client
from keystoneauth1 import identity as keystone_identity
from keystoneauth1 import session as keystone_session
from keystoneclient.v3 import client as keystone_client
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as novaclient

import logging
import os
import random
import time

import utils

logger = logging.getLogger(__name__)


class OfficialClientManager(object):
    """Manager that provides access to the official python clients for
    calling various OpenStack APIs.
    """

    CINDERCLIENT_VERSION = 3
    GLANCECLIENT_VERSION = 2
    KEYSTONECLIENT_VERSION = 3
    NEUTRONCLIENT_VERSION = 2
    NOVACLIENT_VERSION = 2
    INTERFACE = 'admin'
    if "OS_ENDPOINT_TYPE" in list(os.environ.keys()):
        INTERFACE = os.environ["OS_ENDPOINT_TYPE"]

    def __init__(self, username=None, password=None,
                 tenant_name=None, auth_url=None, endpoint_type="internalURL",
                 cert=False, domain="Default", **kwargs):
        self.traceback = ""

        self.client_attr_names = [
            "auth",
            "compute",
            "network",
            "volume",
            "image",
        ]
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self.project_name = tenant_name
        self.auth_url = auth_url
        self.endpoint_type = endpoint_type
        self.cert = cert
        self.domain = domain
        self.kwargs = kwargs

        # Lazy clients
        self._auth = None
        self._compute = None
        self._network = None
        self._volume = None
        self._image = None

    @classmethod
    def _get_auth_session(cls, username=None, password=None,
                          tenant_name=None, auth_url=None, cert=None,
                          domain='Default'):
        if None in (username, password, tenant_name):
            print((username, password, tenant_name))
            msg = ("Missing required credentials for identity client. "
                   "username: {username}, password: {password}, "
                   "tenant_name: {tenant_name}").format(
                username=username,
                password=password,
                tenant_name=tenant_name
            )
            raise msg

        if cert and "https" not in auth_url:
            auth_url = auth_url.replace("http", "https")

        if "v2" in auth_url:
            raise BaseException("Keystone v2 is deprecated since OpenStack"
                                "Queens release. So current OS_AUTH_URL {} "
                                "is not valid. Please use Keystone v3."
                                "".format(auth_url))
        else:
            auth_url = auth_url if ("v3" in auth_url) else "{}{}".format(
                auth_url, "/v3")
            auth = keystone_identity.v3.Password(
                auth_url=auth_url,
                user_domain_name=domain,
                username=username,
                password=password,
                project_domain_name=domain,
                project_name=tenant_name)

        auth_session = keystone_session.Session(auth=auth, verify=cert)
        # auth_session.get_auth_headers()
        return auth_session

    @classmethod
    def get_auth_client(cls, username=None, password=None,
                        tenant_name=None, auth_url=None, cert=None,
                        domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username,
            password=password,
            tenant_name=tenant_name,
            auth_url=auth_url,
            cert=cert,
            domain=domain)
        keystone = keystone_client.Client(version=cls.KEYSTONECLIENT_VERSION,
                                          session=session, **kwargs)
        keystone.management_url = auth_url
        return keystone

    @classmethod
    def get_compute_client(cls, username=None, password=None,
                           tenant_name=None, auth_url=None, cert=None,
                           domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'compute'
        compute_client = novaclient.Client(
            version=cls.NOVACLIENT_VERSION, session=session,
            service_type=service_type, os_cache=False, **kwargs)
        return compute_client

    @classmethod
    def get_network_client(cls, username=None, password=None,
                           tenant_name=None, auth_url=None, cert=None,
                           domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'network'
        return neutron_client.Client(
            service_type=service_type, session=session,
            interface=cls.INTERFACE, **kwargs)

    @classmethod
    def get_volume_client(cls, username=None, password=None,
                          tenant_name=None, auth_url=None, cert=None,
                          domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'volume'
        return cinder_client.Client(
            version=cls.CINDERCLIENT_VERSION,
            service_type=service_type,
            interface=cls.INTERFACE,
            session=session, **kwargs)

    @classmethod
    def get_image_client(cls, username=None, password=None,
                         tenant_name=None, auth_url=None, cert=None,
                         domain='Default', **kwargs):
        session = cls._get_auth_session(
            username=username, password=password, tenant_name=tenant_name,
            auth_url=auth_url, cert=cert, domain=domain)
        service_type = 'image'
        return glance_client.Client(
            version=cls.GLANCECLIENT_VERSION,
            service_type=service_type,
            session=session, interface=cls.INTERFACE,
            **kwargs)

    @property
    def auth(self):
        if self._auth is None:
            self._auth = self.get_auth_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._auth

    @property
    def compute(self):
        if self._compute is None:
            self._compute = self.get_compute_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._compute

    @property
    def network(self):
        if self._network is None:
            self._network = self.get_network_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._network

    @property
    def volume(self):
        if self._volume is None:
            self._volume = self.get_volume_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain, endpoint_type=self.endpoint_type
            )
        return self._volume

    @property
    def image(self):

        if self._image is None:
            self._image = self.get_image_client(
                self.username, self.password, self.tenant_name, self.auth_url,
                self.cert, self.domain
            )
        return self._image


class OSCliActions(object):
    def __init__(self, os_clients):
        self.os_clients = os_clients

    def get_admin_tenant(self):
        # TODO Keystone v3 doesnt have tenants attribute
        return self.os_clients.auth.projects.find(name="admin")

    def get_internal_network(self):
        networks = [
            net for net in self.os_clients.network.list_networks()["networks"]
            if net["admin_state_up"] and not net["router:external"] and
            len(net["subnets"])
            ]
        if networks:
            net = networks[0]
        else:
            net = self.create_network_resources()
        return net

    def create_fake_external_network(self):
        logger.info(
            "Could not find any external network, creating a fake one...")
        net_name = "spt-ext-net-{}".format(random.randrange(100, 999))
        net_body = {"network": {"name": net_name,
                                "router:external": True,
                                "provider:network_type": "local"}}
        try:
            ext_net = \
                self.os_clients.network.create_network(net_body)['network']
            logger.info("Created a fake external net {}".format(net_name))
        except Exception as e:
            # in case 'local' net type is absent, create with default type
            net_body["network"].pop('provider:network_type', None)
            ext_net = \
                self.os_clients.network.create_network(net_body)['network']
        subnet_name = "spt-ext-subnet-{}".format(random.randrange(100, 999))
        subnet_body = {
            "subnet": {
                "name": subnet_name,
                "network_id": ext_net["id"],
                "ip_version": 4,
                "cidr": "10.255.255.0/24",
                "allocation_pools": [{"start": "10.255.255.100",
                                      "end": "10.255.255.200"}]
            }
        }
        self.os_clients.network.create_subnet(subnet_body)
        return ext_net

    def get_external_network(self):
        config = utils.get_configuration()
        ext_net = config.get('external_network') or ''
        if not ext_net:
            networks = [
                net for net in
                self.os_clients.network.list_networks()["networks"]
                if net["admin_state_up"] and net["router:external"] and
                len(net["subnets"])
                ]
        else:
            networks = [net for net in
                        self.os_clients.network.list_networks()["networks"]
                        if net["name"] == ext_net]

        if networks:
            ext_net = networks[0]
            logger.info("Using external net '{}'.".format(ext_net["name"]))
        else:
            ext_net = self.create_fake_external_network()
        return ext_net

    def create_flavor(self, name, ram=256, vcpus=1, disk=2):
        logger.info("Creating a flavor {}".format(name))
        return self.os_clients.compute.flavors.create(name, ram, vcpus, disk)

    def create_sec_group(self, rulesets=None):
        if rulesets is None:
            rulesets = [
                {
                    # ssh
                    'ip_protocol': 'tcp',
                    'from_port': 22,
                    'to_port': 22,
                    'cidr': '0.0.0.0/0',
                },
                {
                    # iperf
                    'ip_protocol': 'tcp',
                    'from_port': 5001,
                    'to_port': 5001,
                    'cidr': '0.0.0.0/0',
                },
                {
                    # iperf3
                    'ip_protocol': 'tcp',
                    'from_port': 5201,
                    'to_port': 5201,
                    'cidr': '0.0.0.0/0',
                },
                {
                    # ping
                    'ip_protocol': 'icmp',
                    'from_port': -1,
                    'to_port': -1,
                    'cidr': '0.0.0.0/0',
                }
            ]
        sg_name = "spt-test-secgroup-{}".format(random.randrange(100, 999))
        sg_desc = sg_name + " SPT"
        secgroup = self.os_clients.compute.security_groups.create(
            sg_name, sg_desc)
        for ruleset in rulesets:
            self.os_clients.compute.security_group_rules.create(
                secgroup.id, **ruleset)
        logger.info("Created a security group {}".format(sg_name))
        return secgroup

    def create_basic_server(self, image=None, flavor=None, net=None,
                            availability_zone=None, sec_groups=(),
                            keypair=None):
        os_conn = self.os_clients
        net = net or self.get_internal_network()
        kwargs = {}
        if sec_groups:
            kwargs['security_groups'] = sec_groups
        server = os_conn.compute.servers.create(
            "spt-test-server-{}".format(random.randrange(100, 999)),
            image, flavor, nics=[{"net-id": net["id"]}],
            availability_zone=availability_zone, key_name=keypair, **kwargs)

        return server

    def get_vm(self, vm_id):
        os_conn = self.os_clients
        try:
            vm = os_conn.compute.servers.find(id=vm_id)
        except Exception as e:
            raise Exception(
                "{}. Could not get the VM \"{}\": {}".format(
                    vm_id, e))
        return vm

    def check_vm_is_active(self, vm_uuid, retry_delay=5, timeout=500):
        vm = None
        timeout_reached = False
        start_time = time.time()
        expected_state = 'ACTIVE'
        while not timeout_reached:
            vm = self.get_vm(vm_uuid)
            if vm.status == expected_state:
                logger.info(
                    "VM {} is in {} status.".format(vm_uuid, vm.status))
                break
            if vm.status == 'ERROR':
                break
            time.sleep(retry_delay)
            timeout_reached = (time.time() - start_time) > timeout
        if vm.status != expected_state:
            logger.info("VM {} is in {} status.".format(vm_uuid, vm.status))
            raise TimeoutError(
                "VM {vm_uuid} on is expected to be in '{expected_state}' "
                "state, but is in '{actual}' state instead.".format(
                    vm_uuid=vm_uuid, expected_state=expected_state,
                    actual=vm.status))

    def create_network(self, tenant_id):
        net_name = "spt-test-net-{}".format(random.randrange(100, 999))
        net_body = {
            'network': {
                'name': net_name,
                'tenant_id': tenant_id
            }
        }
        net = self.os_clients.network.create_network(net_body)['network']
        logger.info("Created internal network {}".format(net_name))
        return net

    def create_subnet(self, net, tenant_id, cidr=None):
        subnet_name = "spt-test-subnet-{}".format(random.randrange(100, 999))
        subnet_body = {
            'subnet': {
                "name": subnet_name,
                'network_id': net['id'],
                'ip_version': 4,
                'cidr': cidr if cidr else '10.1.7.0/24',
                'tenant_id': tenant_id
            }
        }
        subnet = self.os_clients.network.create_subnet(subnet_body)['subnet']
        logger.info("Created subnet {}".format(subnet_name))
        return subnet

    def create_router(self, ext_net, tenant_id):
        name = 'spt-test-router-{}'.format(random.randrange(100, 999))
        router_body = {
            'router': {
                'name': name,
                'external_gateway_info': {
                    'network_id': ext_net['id']
                },
                'tenant_id': tenant_id
            }
        }
        logger.info("Created a router {}".format(name))
        router = self.os_clients.network.create_router(router_body)['router']
        return router

    def create_network_resources(self):
        tenant_id = self.get_admin_tenant().id
        self.get_external_network()
        net = self.create_network(tenant_id)
        self.create_subnet(net, tenant_id)
        return net

    def list_nova_computes(self):
        nova_services = self.os_clients.compute.hosts.list()
        computes_list = [h for h in nova_services if h.service == "compute"]
        return computes_list
