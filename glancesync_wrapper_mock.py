#!/usr/bin/env python
# -- encoding: utf-8 --
#
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FI-Core project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es
#
author = 'jmpr22'

import csv
import glob
import os.path
import shelve
import copy
import os
import argparse
import tempfile
import sys

from glancesync_image import GlanceSyncImage
"""This module contains all the code that interacts directly with the glance
implementation. It isolates the main code from the glance interaction.

Therefore, this module may be changed if the API is upgraded or it is
invoked in a different way, without affecting the main module.

This is a mock implementation, used for testing.
"""


_images = dict()

# Put this property to False to use this file as a mock in a unittest
# when use_persistence is true, image information is preserved in disk.
use_persistence = False
dir_persist = './.glancesync_persist'

def init_persistence(dir=None, clean=False):
    """Function to start using persistence: load the data from the lass
    session if it exists
    :param dir: path of the directory where the persistence files go. Default
     dir is ./.glancesync_persist
    :param clean: if path exists, discard all existing content
    :return:
    """
    global use_persistence, dir_persist, _images
    if dir:
        dir_persist = dir
    use_persistence = True
    _images = dict()
    if os.path.exists(dir):
       for name in glob.glob(dir + '/_persist_*'):
           if clean:
               os.unlink(name)
           else:
               region = os.path.basename(name)[9:]
               _images[region] = shelve.open(name)
    else:
       os.mkdir(dir_persist)

def add_image_to_mock(image):
    """Add the image to the mock
    :param image: The image to add. If can be a GlanceSyncImage or a list
    :return: This method does not return nothing.
    """

    global _images
    if type(image) == list:
        image = GlanceSyncImage.from_field_list(image)
    else:
        image = copy.deepcopy(image)

    if image.region not in _images:
        if use_persistence:
            _images[image.region] = shelve.open(dir_persist + '/_persist_' +
                                                image.region)
        else:
            _images[image.region] = dict()
    _images[image.region][image.id] = image

def add_emptyregion_to_mock(region):
    """Add empty region to mock
    :param image: The image region (e.g. other:Madrid)
    :return: This method does not return nothing.
    """
    if use_persistence:
        _images[region] = shelve.open(dir_persist + '/_persist_' + region)
    else:
        _images[region] = dict()

def add_images_from_csv_to_mock(path):
    """Add images to the mock, reading the csv files saved by the backup tool
    :param path: The directory where the csv files are.
    :return: This method does not return nothing.
    Each file in path has this pattern: backup_<regionname>.csv.
    """

    global _images
    for file in glob.glob(path + '/*.csv'):
        region_name = os.path.basename(file)[7:-4]
        if region_name not in _images:
            if use_persistence:
                _images[region_name] = shelve.open(dir_persist + '/_persist_' +
                                                   region_name)
            else:
                _images[region_name] = dict()
        with open(file) as f:
             for row in csv.reader(f):
                 image = GlanceSyncImage.from_field_list(row)
                 _images[region_name][image.id] = image

def clear_mock():
    global _images
    _images = dict()
    # if using persintence, deleting _persist_ file is responsability of the
    # caller.

def getimagelist(regionobj):
    """return a image list from the glance of the specified region

    :param regionobj: The GlanceSyncRegion object specifying the region to list
    :return: a list of GlanceSyncImage objects
    """
    global _images
    # clone the object: otherwise modifying the returned object
    # modify the object in the _images.
    return copy.deepcopy(_images[regionobj.fullname].values())


def delete_image(regionobj, id, confirm=True):
    """delete a image on the specified region.

    Be careful, this action cannot be reverted and for this reason by
    default requires confirmation!

    :param regionobj: the GlanceSyncRegion object
    :param id: the UUID of the image to delete
    :param confirm: ask for confirmation
    :return: true if image was deleted, false if it was canceled by user
    """
    global _images
    if regionobj.fullname not in _images:
        return False
    images = _images[regionobj.fullname]
    if id not in images:
        return False
    del images[id]
    return True

def update_metadata(regionobj, image):
    """ update the metadata of the image in the specified region
    See GlanceSync.update_metadata_image for more details.

    :param regionobj: region where it is the image to update
    :param image: the image with the metadata to update
    :return: this function doesn't return anything.
    """
    global _images
    images = _images[regionobj.fullname]
    updatedimage = images[image.id]
    updatedimage.is_public = image.is_public
    updatedimage.name = image.name
    #updatedimage.owner = image.owner
    updatedimage.user_properties = dict(image.user_properties)
    if use_persistence:
        images[image.id] = updatedimage


def upload_image(regionobj, image):
    """Upload the image to the glance server on the specified region.

    :param regionobj: GlanceSyncRegion object; the region where the image is
      upload.
    :param image: GlanceSyncImage object; the image to be uploaded.
    :return: the UUID of the new image
    """
    global _images
    count = 1
    if regionobj.fullname not in _images:
        _images[regionobj.fullname] = dict()
    imageid = '1$' + image.name
    while imageid in _images[regionobj.fullname]:
        count += 1
        imageid = str(count) + '$' + image.name
    owner = regionobj.target['tenant']
    new_image = GlanceSyncImage(
        image.name, imageid, regionobj.fullname, owner, image.is_public,
        image.checksum, image.size, image.status, dict(image.user_properties))

    _images[regionobj.fullname][imageid] = new_image
    return imageid

def get_regions(target, target_name, ignore_region=None):
    """It returns the list of regions on the specified target.
    :param target: the target object
    :param target_name: the target name
    :param ignore_region: if specified this region is not included. This is
      used to omit the master region. If there is several regions to omit,
       use the ignored_regions field of the target instead.
    :return: a list of regions. Each region is a string with the prefix
      'target:', unless the target is 'master:'.
    """
    global _images
    all_regions = _images.keys()
    regions_list = list()
    for region in all_regions:
        parts = region.split(':')
        if target_name == 'master':
            if len(parts) != 1:
                continue
            if ignore_region and region == ignore_region:
                continue
        else:
            if len(parts) != 2:
                continue
            if parts[0] != target_name:
                continue
        regions_list.append(region)
    return regions_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Start a clean persistent session'
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--path',  default='~/.glancesync_persist/',
                       help='path where the persistent objects are created')
    group.add_argument('--random', action='store_true',
                       help='create a random path')
    parser.add_argument(
        'initial_load',
        help='directory with initial load, with files (backup_<region>.csv)')
    parser.add_argument(
        '--confirm', action='store_true',
        help='If path exists and it is not empty, this option is required')

    meta = parser.parse_args()
    meta.initial_load = os.path.normpath(os.path.expanduser(meta.initial_load))
    if not os.path.exists(meta.initial_load):
        print >>sys.stderr,\
            'The directory "%s" with the initial load must exist' %\
            meta.initial_load
        sys.exit(-1)

    if meta.random:
        meta.path = tempfile.mkdtemp(prefix='glancesync_tmp')
    else:
        meta.path = os.path.normpath(os.path.expanduser(meta.path))
        m = 'The directory "%s" is not empty. If you are sure, pass --confirm'
        if os.path.exists(meta.path) and not meta.confirm:
            if len(glob.glob(meta.path + '/*')) != 0:
                print >>sys.stderr, m % meta.path
                sys.exit(-1)

    init_persistence(meta.path, True)
    add_images_from_csv_to_mock(meta.initial_load)
    print 'GLANCESYNC_MOCKPERSISTENT_PATH=' + meta.path
