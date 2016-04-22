#!/usr/bin/env python
# -- encoding: utf-8 --
#
# Copyright 2015-2016 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FI-WARE project.
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
__author__ = 'chema'

import unittest
import copy
import StringIO
import logging

from glancesync.glancesync_region import GlanceSyncRegion
from glancesync.glancesync_image import GlanceSyncImage


class TestGlanceSyncRegionBasic(unittest.TestCase):
    def setUp(self):
        self.targets = dict()
        target = dict()
        target['metadata_set'] = set()
        target['forcesyncs'] = set()
        target['metadata_condition'] = None
        target['only_tenant_images'] = False
        target['metadata_set'] = set()
        target['dontupdate'] = set()
        target['replace'] = set()
        target['rename'] = set()
        target['tenant_id'] = 'tenantid'

        # clone
        target2 = dict(target)
        self.targets['master'] = target
        self.targets['other'] = target2
        self.master_region = GlanceSyncRegion('Valladolid', self.targets)
        self.region = GlanceSyncRegion('other:Madrid', self.targets)

    def test_contstructor(self):
        """check that object is constructed without errors and the value of
        fields are ok"""
        master = self.master_region
        region = self.region
        self.assertEquals(master.target, self.targets['master'])
        self.assertEquals(master.region, 'Valladolid')
        self.assertEquals(master.fullname, 'Valladolid')
        self.assertEquals(region.target, self.targets['other'])
        self.assertEquals(region.region, 'Madrid')
        self.assertEquals(region.fullname, 'other:Madrid')


class TestGlanceSyncRegion(unittest.TestCase):
    def create_image(self, region, count, prefix):
        """Helper function for creating a sequence or regions"""
        count = str(count).zfill(2)
        return GlanceSyncImage(
            'image' + count, prefix + count, region, 'tenantid', True,
            'checksum', 1000, 'active', dict())

    def dup_image(self, image, region, count, prefix):
        """Helper function to create an image using another one, but for a
        different region"""
        count = str(count).zfill(2)
        new_image = copy.deepcopy(image)
        new_image.region = region
        new_image.id = prefix + count
        return new_image

    def assertNoWarnings(self):
        """Check that no warnings are generated by the test"""
        self.assertEquals(len(self.buffer_log.getvalue()), 0)

    def assertNumberWarnings(self, number):
        """Check that the number of warnings generated is the expected one"""
        self.assertEquals(len(self.buffer_log.getvalue().splitlines()), number)

    def setUp(self):
        # Capture warnings
        logger = logging.getLogger('GlanceSync-Client')
        self.buffer_log = StringIO.StringIO()
        handler = logging.StreamHandler(self.buffer_log)
        logger.addHandler(handler)

        # Create master region dict
        self.master_region_dict = master_region_dict = dict()
        for i in range(11):
            image1 = self.create_image('Valladolid', i, '0')
            master_region_dict[image1.name] = image1

        # Make particular cases in the images
        master_region_dict['image00'].is_public = False
        master_region_dict['image00'].user_properties['okhronisable'] = True

        master_region_dict['image01'].user_properties['okhronisable'] = True
        master_region_dict['image01'].user_properties['key1'] = 1000

        master_region_dict['image02'].user_properties['okhronisable'] = True
        master_region_dict['image01'].user_properties['key1'] = 2000
        master_region_dict['image01'].user_properties['key2'] = 0

        master_region_dict['image03'].user_properties['okhronisable'] = True
        master_region_dict['image03'].user_properties['kernel_id'] = 'image01'
        master_region_dict['image03'].user_properties['ramdisk_id'] = 'image02'

        master_region_dict['image04'].user_properties['okhronisable'] = True
        master_region_dict['image04'].user_properties['domain'] = 'acl3'

        master_region_dict['image05'].user_properties['okhronisable'] = True
        master_region_dict['image05'].user_properties['zone'] = 'acl4'

        master_region_dict['image06'].user_properties['p1'] = 30
        master_region_dict['image06'].is_public = False

        master_region_dict['image07'].size = 100000
        master_region_dict['image07'].user_properties['okhronisable'] = True
        master_region_dict['image07'].user_properties['p1'] = 40

        master_region_dict['image08'].size = 5000
        master_region_dict['image08'].user_properties['okhronisable'] = False

        master_region_dict['image09'].user_properties['okhronisable'] = True

        master_region_dict['image10'].is_public = False

        # Now, build the region dict using the same values
        self.region_dict = region_dict = dict()
        for i in range(11):
            image_master = master_region_dict['image' + str(i).zfill(2)]
            image_region = self.dup_image(image_master, 'Burgos', i, '1')
            region_dict[image_region.name] = image_region

        # Fix kernel_id and ramdisk_id of regional images
        region_dict['image03'].user_properties['kernel_id'] = '101'
        region_dict['image03'].user_properties['ramdisk_id'] = '102'
        region_dict['image09'].user_properties['ramdisk_id'] = '104'

        # changes some values in properties: the values included in meta_set
        # should affect, but not the others...
        region_dict['image01'].user_properties['key1'] = 1
        region_dict['image02'].user_properties['key2'] = 1
        self.targets = dict()
        target = dict()
        # in this case we use metadata_set as 'forbidden' properties
        target['metadata_set'] = set(['key1'])
        target['forcesyncs'] = set()
        cond = "image.user_properties.get('okhronisable',False) and\
         not set(image.user_properties.keys()).intersection(set(['domain',\
        'zone'])) and image.size < 10000"
        target['metadata_condition'] = compile(cond, '', 'eval')
        target['only_tenant_images'] = False
        target['tenant_id'] = 'tenantid'
        target['dontupdate'] = set()
        target['replace'] = set()
        target['rename'] = set()

        self.targets['master'] = target
        self.master_region = GlanceSyncRegion('Valladolid', self.targets)
        self.region = GlanceSyncRegion('Burgos', self.targets)

        # Expected result of imges_to_sync_dict call
        self.expected_images_to_sync_dict = {
            'image00': self.master_region_dict['image00'],
            'image01': self.master_region_dict['image01'],
            'image02': self.master_region_dict['image02'],
            'image03': self.master_region_dict['image03'],
            'image09': self.master_region_dict['image09'],
        }

    def test_images_to_sync_dict_default(self):
        """test method images_to_sync_dict, without metadata_set nor
        metadata_condition"""
        self.targets['master']['metadata_set'] = set()
        self.targets['master']['metadata_condition'] = None
        new_dict = self.region.images_to_sync_dict(self.master_region_dict)
        expected = set(['image01', 'image02', 'image03', 'image04', 'image05',
                        'image07', 'image08', 'image09'])
        self.assertEquals(expected, set(new_dict.keys()))
        self.targets['master']['forcesyncs'] = set(['000', '010'])
        expected.add('image10')
        expected.add('image00')
        new_dict = self.region.images_to_sync_dict(self.master_region_dict)
        self.assertEquals(expected, set(new_dict.keys()))
        self.assertNoWarnings()

    def test_images_to_sync_dict_metadata(self):
        """test method images_to_sync_dict, without metadata_condition but
        with medata_set"""
        self.targets['master']['metadata_set'] = set(['p1'])
        self.targets['master']['metadata_condition'] = None
        new_dict = self.region.images_to_sync_dict(self.master_region_dict)
        expected = set(['image07'])
        self.assertEquals(expected, set(new_dict.keys()))
        self.assertNoWarnings()

    def test_images_to_sync_dict_func(self):
        """test method images_to_sync, with metadata_condition (see setUp)"""
        new_dict = self.region.images_to_sync_dict(self.master_region_dict)
        expected = set(['image00', 'image01', 'image02', 'image03', 'image09'])
        self.assertEquals(expected, set(new_dict.keys()))
        self.assertNoWarnings()

    def test_local_images_filtered(self):
        """test method region_filtered"""
        region_filtered = self.region.local_images_filtered(
            self.expected_images_to_sync_dict, self.region_dict.values())
        expected = set(['image00', 'image01', 'image02', 'image03', 'image09'])
        self.assertEquals(expected, set(region_filtered.keys()))
        self.assertNoWarnings()

    def test_local_images_filtered_owner(self):
        """Don't accept image if owner is not the tenant"""
        self.region_dict['image00'].owner = 'othertenantid'
        self.region.target['only_tenant_images'] = True
        region_filtered = self.region.local_images_filtered(
            self.expected_images_to_sync_dict, self.region_dict.values())
        expected = set(['image01', 'image02', 'image03', 'image09'])
        self.assertEquals(expected, set(region_filtered.keys()))
        self.assertNumberWarnings(1)

    def test_local_images_filtered_owner_warning(self):
        """Accept image owned by another tenant, but check warning"""
        self.region_dict['image00'].owner = 'othertenantid'
        region_filtered = self.region.local_images_filtered(
            self.expected_images_to_sync_dict, self.region_dict.values())
        expected = set(['image00', 'image01', 'image02', 'image03', 'image09'])
        self.assertEquals(expected, set(region_filtered.keys()))
        self.assertNumberWarnings(1)

    def test_local_images_filtered_duplicated(self):
        """Check warning because duplicated name"""
        region_list = self.region_dict.values()
        image_new = self.dup_image(self.region_dict['image00'], 'Burgos',
                                   11, '0')
        region_list.append(image_new)
        region_filtered = self.region.local_images_filtered(
            self.expected_images_to_sync_dict, region_list)
        expected = set(['image00', 'image01', 'image02', 'image03', 'image09'])
        self.assertEquals(expected, set(region_filtered.keys()))
        self.assertNumberWarnings(1)

    def test_local_images_filtered_duplicated_checksum(self):
        """Check that if there is a duplicated name, but one of them has the
        right checksum, the image with the right checksum is used. This is
        independent of the warning"""
        region_list = self.region_dict.values()
        image_new_1 = self.dup_image(self.region_dict['image00'], 'Burgos',
                                   11, '0')
        image_new_2 = self.dup_image(self.region_dict['image00'], 'Burgos',
                                   12, '0')
        image_new_3 = self.dup_image(self.region_dict['image00'], 'Burgos',
                                   13, '0')

        image_new_2.checksum = self.region_dict['image00'].checksum
        image_new_1.checksum = 'otherchecksum'
        image_new_3.checksum = 'otherchecksum'
        region_list = list()
        region_list.append(image_new_1)
        region_list.append(image_new_2)
        region_list.append(image_new_3)

        region_filtered = self.region.local_images_filtered(
            self.expected_images_to_sync_dict, region_list)
        images_ids = set(image.id for image in region_filtered.values())
        self.assertIn('012', images_ids)
        self.assertNotIn('011', images_ids)
        self.assertNotIn('013', images_ids)
        self.assertNumberWarnings(2)

    def test_image_list_to_sync(self):
        """ This function involves calling both images_to_sync_dict and
        local_images_filtered and a pair of methods of GlanceSyncRegion; it is
        more an integration function.
        """
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('pending_metadata', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('ok', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_missing(self):
        """ Check with one image missing; this implies also metadata missing
        of image03, because its kernel_id points to the missing image.
        """
        del(self.region_dict['image01'])
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('pending_upload', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('pending_ami', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_missing(self):
        """ Check with one image not active; this should be equivalent to
        a missing image, but also a warning is generated.
        """
        self.region_dict['image01'].status = 'pending'
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('pending_upload', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('pending_ami', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_checksum_error(self):
        """ Check with one image with different checksum
        """
        self.region_dict['image01'].checksum = 'otherchecksum'
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('error_checksum', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('ok', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_checksum_dont_update(self):
        """ Check with one image with different checksum, but included in
        dontupdate
        """
        self.region.target['dontupdate'] = set(['otherchecksum'])
        self.region_dict['image01'].checksum = 'otherchecksum'
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('ok_stalled_checksum', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('ok', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_checksum_replace(self):
        """ Check with one image with different checksum
        """
        self.region.target['replace'] = set(['otherchecksum'])
        self.region_dict['image01'].checksum = 'otherchecksum'
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('pending_replace', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('pending_ami', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_checksum_rename(self):
        """ Check with one image with different checksum
        """
        self.region.target['rename'] = set(['otherchecksum'])
        self.region_dict['image01'].checksum = 'otherchecksum'
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('pending_rename', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('pending_ami', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_checksum_mixed(self):
        """ Check with one image with different checksum
        """
        self.region.target['dontupdate'] = set(['checksum1'])
        self.region.target['replace'] = set(['checksum2', 'any'])
        self.region.target['rename'] = set(['any'])
        self.region_dict['image01'].checksum = 'checksum1'
        self.region_dict['image00'].checksum = 'checksum2'
        self.region_dict['image03'].checksum = 'checksum3'
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('pending_replace', self.region_dict['image00']),
            ('ok_stalled_checksum', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('pending_rename', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_ami(self):
        """Check changing ramdisk_id of image03 to point to a wrong, but
         existing image and image09 to a image that is not in the
         synchronisation set"""
        self.region_dict['image03'].user_properties['ramdisk_id'] = '101'
        self.master_region_dict['image09'].user_properties['kernel_id'] =\
            'image04'

        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('ok', self.region_dict['image00']),
            ('pending_metadata', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('pending_metadata', self.region_dict['image03']),
            ('error_ami', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)

    def test_image_list_to_sync_private(self):
        """Check image is_public differences between master and region"""
        self.master_region_dict['image00'].is_public = False
        self.region_dict['image00'].is_public = True
        self.master_region_dict['image01'].is_public = False
        self.region_dict['image01'].is_public = True
        result = self.region.image_list_to_sync(self.master_region_dict,
                                                self.region_dict.values())
        expected = [
            ('pending_metadata', self.region_dict['image00']),
            ('pending_metadata', self.region_dict['image01']),
            ('ok', self.region_dict['image02']),
            ('ok', self.region_dict['image03']),
            ('pending_metadata', self.region_dict['image09'])]
        result_as_list = list(x[1].name + '_' + x[0] for x in result)
        expected_as_list = list(x[1].name + '_' + x[0] for x in expected)
        self.assertEqual(expected_as_list, result_as_list)


class TestGlanceSyncRegionObsoletedImages(unittest.TestCase):
    def _create_images(self, name):
        """Create a pair or images, one on each region"""
        image1 = GlanceSyncImage(
            name, 'id_VA_' + name, 'Valladolid', 'VA_tenant1', True,
            'checksum', 1000, 'active', dict())
        image1.is_public = False

        image2 = GlanceSyncImage(
            name, 'id_BU_' + name, 'Burgos', 'BU_tenant1', True,
            'checksum', 1000, 'active', dict())
        image2.is_public = False

        return image1, image2

    def setUp(self):
        """constructor"""
        self.master_region_dict = dict()
        self.images_region = list()
        target_master = {'tenant_id': 'VA_tenant1'}
        target_other = {'tenant_id': 'BU_tenant1'}
        self.targets = dict()
        self.targets['master'] = target_master
        self.targets['other'] = target_other
        target_other['metadata_set'] = set(['sync'])
        target_other['forcesyncs'] = list()

        self.master_region = GlanceSyncRegion('Valladolid', self.targets)
        self.region = GlanceSyncRegion('other:Burgos', self.targets)

    def test_images_list_to_obsolete_notfound(self):
        """No images with _obsolete suffix in master"""
        (image1, image2) = self._create_images('image1')
        self.master_region_dict[image1.name] = image1
        self.images_region.append(image2)
        (image1, image2) = self._create_images('image2')
        image2.name = 'image2_obsolete'
        self.master_region_dict[image1.name] = image2
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertFalse(result)

    def test_images_list_to_obsolete_notfound_checksum(self):
        """Image found, but bad checksum"""
        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        image2.name = 'image1'
        image2.checksum = 'other_checksum'
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertFalse(result)

    def test_images_list_to_obsolete_notfound_checksum(self):
        """Image found, but bad owner"""
        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        image2.name = 'image1'
        image2.owner = 'other_owner'
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertFalse(result)

    def test_images_list_to_obsolete_found_alreadydone(self):
        """Found image obsolete, but already renamed and has the same meta
        """
        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertFalse(result)

    def test_images_list_to_obsolete_found_pending_rename(self):
        """Found image to rename"""
        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        image2.name = 'image1'
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertTrue(len(result) == 1)

    def test_images_list_to_obsolete_found_pending_public(self):
        """Found image already renamed, but public"""
        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        image2.is_public = True
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertTrue(len(result) == 1)
        self.assertFalse(result[0].is_public)

    def test_images_list_to_obsolete_found_pending_metadata(self):
        """Found image already renamed, but different metadata"""
        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        image1.user_properties['key1'] = 'value1'
        image2.user_properties['key1'] = 'value2'
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region, set(['key1']))
        self.assertTrue(len(result) == 1)
        self.assertEquals(result[0].user_properties['key1'], 'value1')

    def test_images_list_to_obsolete_warning(self):
        """there is an image_obsoleted, but also exists image and it is
        synchronisable"""

        # Capture warnings
        logger = logging.getLogger('GlanceSync-Client')
        self.buffer_log = StringIO.StringIO()
        handler = logging.StreamHandler(self.buffer_log)
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)

        (image1, image2) = self._create_images('image1_obsolete')
        self.master_region_dict[image1.name] = image1
        (image1, image2) = self._create_images('image1')
        image1.user_properties['sync'] = True
        image1.is_public = True
        self.master_region_dict[image1.name] = image1
        self.images_region.append(image2)
        result = self.region.image_list_to_obsolete(
            self.master_region_dict, self.images_region)
        self.assertFalse(result)
        msg = 'Ignore obsolete master image image1_obsolete because image1 '\
              'exists and it is synchronisable.'
        self.assertEquals(self.buffer_log.getvalue().strip(), msg)