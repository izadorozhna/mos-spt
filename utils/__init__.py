import os
import yaml

from utils import os_client


def compile_pairs(nodes):
    result = {}
    if len(nodes) %2 != 0:
        nodes.pop(1)
    pairs = zip(*[iter(nodes)]*2)
    for pair in pairs:
        result[pair[0]+'<>'+pair[1]] = pair
    return result


def get_pairs():
    config = get_configuration()
    cmp_hosts = config.get('CMP_HOSTS') or []
    skipped_nodes = config.get('skipped_nodes') or []
    if skipped_nodes:
        print("Notice: {0} nodes will be skipped for vm2vm test").format(skipped_nodes)
    if not cmp_hosts:
        openstack_clients = os_client.OfficialClientManager(
            username=os.environ['OS_USERNAME'],
            password=os.environ['OS_PASSWORD'],
            tenant_name=os.environ['OS_PROJECT_NAME'],
            auth_url=os.environ['OS_AUTH_URL'],
            cert=False,
            domain=os.environ['OS_PROJECT_DOMAIN_NAME']
        )
        os_actions = os_client.OSCliActions(openstack_clients)
        nova_computes = os_actions.list_nova_computes()
        # TODO(izadorozhna): remove the workaround for 1 compute
        # if len(nova_computes) < 2:
        #     raise BaseException(
        #         "At least 2 compute hosts are needed for VM2VM test, "
        #         "now: {}.".format(len(nova_computes)))
        cmp_hosts = [n.host_name for n in nova_computes]
        #TODO(izadorozhna): remove the workaround for 1 compute
        cmp_hosts.append(nova_computes[0].host_name)

    return compile_pairs(cmp_hosts)


def get_configuration():
    """function returns configuration for environment
    and for test if it's specified"""

    global_config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../global_config.yaml")
    with open(global_config_file, 'r') as file:
        global_config = yaml.load(file, Loader=yaml.SafeLoader)
    for param in global_config.keys():
        if param in os.environ.keys():
            if ',' in os.environ[param]:
                global_config[param] = []
                for item in os.environ[param].split(','):
                    global_config[param].append(item)
            else:
                global_config[param] = os.environ[param]

    return global_config