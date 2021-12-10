import pytest
import time
import subprocess
import random
import logging

import utils

logger = logging.getLogger(__name__)


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
    image_size_megabytes = utils.get_configuration().get("IMAGE_SIZE_MB", 2000)
    create_file_cmdline = 'dd if=/dev/zero of=/tmp/image_mk_framework.dd ' \
                          'bs=1M count={} 2>/dev/null' \
                          ''.format(image_size_megabytes)
    is_cmd_successful = subprocess.call(create_file_cmdline, shell=True) == 0
    logger.info("Created local image file /tmp/image_mk_framework.dd")
    yield is_cmd_successful

    # teardown
    logger.info("Deleting /tmp/image_mk_framework.dd file")
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
        pytest.fail("Can't convert IMAGE_SIZE_MB={} to 'int'".format(
            image_size_megabytes))
    image_size_megabytes = int(image_size_megabytes)
    if not create_image:
        pytest.skip("Can't create image, maybe there is lack of disk "
                    "space to create file {}MB".
                    format(image_size_megabytes))
    image_name = "spt-test-image-{}".format(random.randrange(100, 999))
    try:
        image = openstack_clients.image.images.create(
            name=image_name,
            disk_format='iso',
            container_format='bare')
        logger.info("Created an image {} in Glance.".format(image_name))
    except BaseException as e:
        logger.info("Could not create image in Glance. See details: {}"
                    "".format(e))
        pytest.fail("Can't create image in Glance. Occurred error: {}"
                    "".format(e))

    logger.info("Testing upload file speed...")
    start_time = time.time()
    try:
        openstack_clients.image.images.upload(
            image.id, image_data=open("/tmp/image_mk_framework.dd", 'rb'))
    except BaseException as e:
        pytest.fail("Can't upload image in Glance. "
                    "Occurred error: {}".format(e))
    end_time = time.time()

    speed_upload = image_size_megabytes / (end_time - start_time)

    logger.info("Testing download file speed...")
    start_time = time.time()
    with open("/tmp/image_mk_framework.download", 'wb') as image_file:
        for item in openstack_clients.image.images.data(image.id):
            image_file.write(item)
    end_time = time.time()

    speed_download = image_size_megabytes / (end_time - start_time)
    logger.info("Deleted image {}.".format(image.id))
    openstack_clients.image.images.delete(image.id)
    record_property("Upload", speed_upload)
    record_property("Download", speed_download)

    print("++++++++++++++++++++++++++++++++++++++++")
    print(('upload - {} MB/s'.format(speed_upload)))
    print(('download - {} MB/s'.format(speed_download)))
    print("++++++++++++++++++++++++++++++++++++++++")
