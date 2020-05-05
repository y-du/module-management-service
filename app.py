"""
   Copyright 2020 Yann Dumont

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from manager.logger import initLogger
from manager.configuration import cm_conf
from manager.worker import WorkerManager
from manager import api
import snorkels
import os
import falcon


initLogger(cm_conf.Logger.level)

local_storage = "{}/data".format(os.getcwd())

if not os.path.exists(local_storage):
    os.makedirs(local_storage)

ps_adapter = snorkels.ps_adapter.SQLlite3Adapter(db_name="storage", user_path=local_storage)
kvs = snorkels.KeyValueStore(name="storage", ps_adapter=ps_adapter)

wm = WorkerManager()

app = falcon.API()

app.req_options.strip_url_path_trailing_slash = True

routes = (
    ("/modules", api.Modules(kvs)),
    ("/modules/{module}", api.Module(kvs, wm))
)

for route in routes:
    app.add_route(*route)
