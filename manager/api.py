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

__all__ = ("Components", "Component")


from .logger import getLogger
from .configuration import cm_conf, EnvVars
from .util import ComponentState, parseComponent, activateComponent, deactivateComponent, removeComponent
from .worker import WorkerManager
import snorkels
import requests
import falcon
import json


logger = getLogger(__name__.split(".", 1)[-1])


def reqDebugLog(req):
    logger.debug("method='{}' path='{}' content_type='{}'".format(req.method, req.path, req.content_type))


def reqErrorLog(req, ex):
    logger.error("method='{}' path='{}' - {}".format(req.method, req.path, ex))


class ConflictError(Exception):
    pass


class Components:
    def __init__(self, kvs: snorkels.KeyValueStore):
        self.__kvs = kvs

    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response):
        reqDebugLog(req)
        try:
            data = dict()
            for key in self.__kvs.keys():
                data[key.decode()] = json.loads(self.__kvs.get(key))
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.body = json.dumps(data)
        except Exception as ex:
            resp.status = falcon.HTTP_500
            reqErrorLog(req, ex)

    def on_post(self, req: falcon.request.Request, resp: falcon.response.Response):
        reqDebugLog(req)
        if not req.content_type == falcon.MEDIA_JSON:
            resp.status = falcon.HTTP_415
            reqErrorLog(req, "wrong content type - '{}'".format(req.content_type))
        else:
            try:
                data = json.load(req.bounded_stream)
                if data["id"] == EnvVars.ComponentID.value:
                    raise ConflictError
                try:
                    cd = json.loads(self.__kvs.get(data["id"]))
                    if cd["state"] == ComponentState.active:
                        raise Exception("can't update active component '{}'".format(data["id"]))
                except snorkels.GetError:
                    pass
                cmp_data, configs = parseComponent(data)
                response = requests.put(
                    url="{}/{}/{}".format(cm_conf.CS.url, cm_conf.CS.api, data["id"]),
                    json=configs
                )
                if response.status_code == 200:
                    cmp_data["state"] = ComponentState.inactive
                    self.__kvs.set(data["id"], json.dumps(cmp_data))
                else:
                    raise Exception("storing configs failed for '{}' - {}".format(data["id"], response.status_code))
                resp.status = falcon.HTTP_200
            except ConflictError:
                resp.status = falcon.HTTP_409
                reqErrorLog(req, "component conflict")
            except KeyError as ex:
                resp.status = falcon.HTTP_400
                reqErrorLog(req, ex)
            except Exception as ex:
                resp.status = falcon.HTTP_500
                reqErrorLog(req, ex)


class Component:
    def __init__(self, kvs: snorkels.KeyValueStore, wm: WorkerManager):
        self.__kvs = kvs
        self.__wm = wm

    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, component):
        reqDebugLog(req)
        try:
            data = self.__kvs.get(component)
            resp.content_type = falcon.MEDIA_JSON
            resp.body = data.decode()
            resp.status = falcon.HTTP_200
        except snorkels.GetError as ex:
            resp.status = falcon.HTTP_404
            reqErrorLog(req, ex)
        except Exception as ex:
            resp.status = falcon.HTTP_500
            reqErrorLog(req, ex)

    def on_patch(self, req: falcon.request.Request, resp: falcon.response.Response, component):
        reqDebugLog(req)
        if not req.content_type == falcon.MEDIA_JSON:
            resp.status = falcon.HTTP_415
            reqErrorLog(req, "wrong content type - '{}'".format(req.content_type))
        else:
            try:
                data = json.load(req.bounded_stream)
                cmp_data = json.loads(self.__kvs.get(component))
                worker = self.__wm.getWorker(component)
                if data["state"] == ComponentState.active:
                    if not data["state"] == cmp_data["state"]:
                        response = requests.get(url="{}/{}/{}".format(cm_conf.CS.url, cm_conf.CS.api, component))
                        if response.status_code == 200:
                            configs = response.json()
                            worker.setTask(activateComponent, kvs=self.__kvs, cmp=component, configs=configs, cmp_data=cmp_data)
                            worker.start()
                        else:
                            raise Exception("can't retrieve configs for '{}' - {}".format(component, response.status_code))
                elif data["state"] == ComponentState.inactive:
                    if not data["state"] == cmp_data["state"]:
                        worker.setTask(deactivateComponent, kvs=self.__kvs, cmp=component, cmp_data=cmp_data)
                        worker.start()
                else:
                    raise ValueError("unknown state '{}'".format(data["state"]))
                resp.status = falcon.HTTP_200
            except KeyError as ex:
                resp.status = falcon.HTTP_400
                reqErrorLog(req, ex)
            except snorkels.GetError as ex:
                resp.status = falcon.HTTP_404
                reqErrorLog(req, ex)
            except Exception as ex:
                resp.status = falcon.HTTP_500
                reqErrorLog(req, ex)

    def on_delete(self, req: falcon.request.Request, resp: falcon.response.Response, component):
        reqDebugLog(req)
        try:
            cmp_data = json.loads(self.__kvs.get(component))
            if cmp_data["state"] == ComponentState.active:
                raise Exception("can't remove active component")
            response = requests.delete(url="{}/{}/{}".format(cm_conf.CS.url, cm_conf.CS.api, component))
            if response.status_code == 200:
                worker = self.__wm.getWorker(component)
                worker.setTask(removeComponent, kvs=self.__kvs, cmp=component, cmp_data=cmp_data)
                worker.start()
            else:
                raise Exception("can't remove configs for '{}' - {}".format(component, response.status_code))
            resp.status = falcon.HTTP_200
        except snorkels.DeleteError as ex:
            resp.status = falcon.HTTP_404
            reqErrorLog(req, ex)
        except Exception as ex:
            resp.status = falcon.HTTP_500
            reqErrorLog(req, ex)
