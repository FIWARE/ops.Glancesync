#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from app import app, db
from app.settings.settings import HOST, PORT

__author__ = 'fla'

migrate = Migrate(app, db)

# Add the db and runserver commands
manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(host=HOST, port=PORT, use_debugger=True))

if __name__ == '__main__':
    manager.run()
