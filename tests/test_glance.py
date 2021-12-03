import pytest
import time
import subprocess
import utils


def is_parsable(value, to):
    """
    Check if value can be converted into some type
    :param value:  input value that should be converted
    :param to: type of output value like int, float. It's not a string!
    :return: bool
    """
    try:
        to(value)
    except:
        return False
    return True


@pytest.fixture
def create_image():
    image_size_megabytes = utils.get_configuration().get("IMAGE_SIZE_MB")
    create_file_cmdline = 'dd if=/dev/zero of=/tmp/image_mk_framework.dd bs=1M count={image_size}'.format(
        image_size=image_size_megabytes)

    is_cmd_successful = subprocess.call(create_file_cmdline, shell=True) == 0
    yield is_cmd_successful
    # teardown
    subprocess.call('rm -f /tmp/image_mk_framework.dd', shell=True)
    subprocess.call('rm -f /tmp/image_mk_framework.download', shell=True)


def test_speed_glance(create_image, openstack_clients, record_property):
    """
    Simplified Performance Tests Download / upload Glance
    1. Create file with random data (dd)
    2. Upload data as image to glance.
    3. Download image.
    4. Measure download/upload speed and print them into stdout
    """
    image_size_megabytes = utils.get_configuration().get("IMAGE_SIZE_MB")
    if not is_parsable(image_size_megabytes, int):
        pytest.fail("Can't convert IMAGE_SIZE_MB={} to 'int'".format(image_size_megabytes))
    image_size_megabytes = int(image_size_megabytes)
    if not create_image:
        pytest.skip("Can't create image, maybe there is lack of disk space to create file {}MB".
                    format(image_size_megabytes))
    try:
        image = openstack_clients.image.images.create(
            name="test_image",
            disk_format='iso',
            container_format='bare')
    except BaseException as e:
        pytest.fail("Can't create image in Glance. Occurred error: {}".format(e))

    # FIXME: Error may happens while executing images.upload:
    #  CommunicationError: Error finding address for
    #  http://os-ctl-vip.harhipova-cicd-os-test.local:9292/v2/images/8bce33dd-9837-4646-b747-7f7f5ce01092/file: Unable to establish connection to http://os-ctl-vip.harhipova-cicd-os-test.local:9292/v2/images/8bce33dd-9837-4646-b747-7f7f5ce01092/file: [Errno 32] Broken pipe
    # This may happen because of low disk space on ctl node or old cryptography package
    # (will be fixed after upgrading to Python3)
    start_time = time.time()
    try:
        openstack_clients.image.images.upload(
            image.id,
            image_data=open("/tmp/image_mk_framework.dd", 'rb'))
    except BaseException as e:
        pytest.fail("Can't upload image in Glance. Occurred error: {}".format(e))
    end_time = time.time()

    speed_upload = image_size_megabytes / (end_time - start_time)

    start_time = time.time()
    # it creates new file /tmp/image_mk_framework.download . It should be removed in teardown
    with open("/tmp/image_mk_framework.download", 'wb') as image_file:
        for item in openstack_clients.image.images.data(image.id):
            image_file.write(item)
    end_time = time.time()

    speed_download = image_size_megabytes / (end_time - start_time)

    openstack_clients.image.images.delete(image.id)
    record_property("Upload", speed_upload)
    record_property("Download", speed_download)

    print("++++++++++++++++++++++++++++++++++++++++")
    print('upload - {} Mb/s'.format(speed_upload))
    print('download - {} Mb/s'.format(speed_download))
