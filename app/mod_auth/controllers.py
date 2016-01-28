#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FI-WARE project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
#        http://www.apache.org/licenses/LICENSE-2.0
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

# Import flask dependencies
from flask import Blueprint, Response, abort
import httplib

# Import the database object from the main app module
from app import db

# Import module models (i.e. User)
from models import User

# Import authentication decorator
from openstack_auth import authorized
from app.settings.settings import CONTENT_TYPE
from app.mod_auth.models import Images, Task
from app.settings.log import logger

__author__ = 'fla'

# Define the blueprint: 'auth', set its url prefix: app.url/regions
mod_auth = Blueprint('auth', __name__, url_prefix='/regions')


# Set the route and accepted methods
@mod_auth.route('/<regionid>', methods=['GET'])
@authorized
def get_status(regionid, token):
    """
    Lists information the status of the synchronization of the images in
    the region <regionid>. Keep in mind that <regionid> is the name of
    the region.
    :param regionid: Region name how you can obtain from the Keystone
                     service. Example: Spain2.
    :return: JSON response message with the detailed information about
             the images and the sincronization status.
    """

    message = "GET, get information about the synchronization status in the region: {}".format(regionid)

    logger.info(message)

    # Just for check this data should be returned by glancesync client
    x = Images()

    value = ['3cfeaf3f0103b9637bb3fcfe691fce1e', 'base_ubuntu_14.04', 'ok', None]
    x.add(value)

    value = ['4rds4f3f0103b9637bb3fcfe691fce1e', 'base_centOS_7', 'ok', None]
    x.add(value)

    return Response(response=x.dump(),
                    status=httplib.OK,
                    content_type=CONTENT_TYPE)


@mod_auth.route('/<regionid>', methods=['POST'])
@authorized
def synchronize(regionid, token):
    """
    Synchronize the images of the corresponding region defined by its regionId.
    The operation is asynchronous a response a taskId in order that you can follow
    the execution of the process.
    :param regionid: Region name how you can obtain from the Keystone
                     service. Example: Spain2.
    :return: JSON message with the identification of the created task
    """
    # WARNING
    # It is for testing only, the functionality of this method is create a new Task,
    # store the content of the new task with <taskid> in DB with status 'syncing'
    # and launch a fork to start the execution of the synchronization process. At the
    # end of the synchronization process, we update the DB registry with the status
    # 'synced'
    message = "POST, create a new synchronization task in the region: {}".format(regionid)

    logger.info(message)

    newtask = Task(status='syncing')

    # name and role should be returned from authorized operation, to be extended in Sprint 16.02
    newuser = User(name=token.username, taskid=str(newtask.taskid), role='admin', status=newtask.status)

    db.session.add(newuser)
    db.session.commit()

    return Response(response=newtask.dump(),
                    status=httplib.OK,
                    content_type=CONTENT_TYPE)


@mod_auth.route('/<regionid>/tasks/<taskid>', methods=['GET'])
@authorized
def get_task(regionid, taskid, token):
    """

    :param regionid:
    :param taskid:
    :return:
    """
    # WARNING
    # It is for test only, we have to recover this information from the DB
    # in order to know the status of the synchronization of the task <taskid>
    message = "GET, obtain the status of the synchronization of a task: {} in the region: {}".format(taskid, regionid)

    logger.info(message)

    users = User.query.filter(User.task_id == taskid).all()

    if not users:
        abort(httplib.NOT_FOUND)
    else:
        newtask = Task(taskid=users[0].task_id, status=users[0].status)

        return Response(response=newtask.dump(),
                        status=httplib.OK,
                        content_type=CONTENT_TYPE)


@mod_auth.route('/<regionid>/tasks/<taskid>', methods=['DELETE'])
@authorized
def delete_task(regionid, taskid, token):

    message = "DELETE, delete the registry of task {} in the region: {}".format(taskid, regionid)

    logger.info(message)

    users = User.query.filter(User.task_id == taskid).all()

    if not users:
        abort(httplib.NOT_FOUND)
    else:
        db.session.delete(users[0])
        db.session.commit()

    return Response(response=None,
                    status=httplib.OK,
                    content_type=CONTENT_TYPE)
