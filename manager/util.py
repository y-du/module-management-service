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


from .configuration import cm_conf, EnvVars
import snorkels
import typing
import json
import requests


__all__ = ("ComponentState", "parseComponent", "activateComponent", "deactivateComponent", "removeComponent")


class ComponentState:
    active = "active"
    inactive = "inactive"


def parseComponent(cmp: dict) -> typing.Tuple[dict, dict]:
    cmp_data = {
        "name": cmp["name"],
        "description": cmp["description"],
        "services": {key: {"hash": srv["hash"]} for key, srv in cmp["services"].items()},
        "hash": cmp["hash"]
    }
    configs = dict()
    for key, srv in cmp["services"].items():
        del srv["hash"]
        configs[key] = srv
    return cmp_data, configs


def activateComponent(kvs: snorkels.KeyValueStore, cmp: str, configs: dict, cmp_data):
    err = False
    for srv, config in configs.items():
        config["name"] = srv
        config["runtime_vars"] = {
            EnvVars.ComponentID.name: cmp,
            EnvVars.GatewayLocalIP.name: EnvVars.GatewayLocalIP.value
        }
        response = requests.post(url="{}/{}".format(cm_conf.DM.url, cm_conf.DM.api), json=config)
        if not response.status_code == 200:
            err = True
            break
    if not err:
        for srv in configs:
            response = requests.patch(url="{}/{}/{}".format(cm_conf.DM.url, cm_conf.DM.api, srv), json={"state": "running"})
            if not response.status_code == 200:
                err = True
                break
    if not err:
        cmp_data["state"] = ComponentState.active
        kvs.set(cmp, json.dumps(cmp_data))


def deactivateComponent(kvs: snorkels.KeyValueStore, cmp: str, cmp_data):
    err = False
    for srv in cmp_data["services"]:
        response = requests.patch(url="{}/{}/{}".format(cm_conf.DM.url, cm_conf.DM.api, srv), json={"state": "stopped"})
        if not response.status_code == 200:
            err = True
            break
    if not err:
        cmp_data["state"] = ComponentState.inactive
        kvs.set(cmp, json.dumps(cmp_data))


def removeComponent(kvs: snorkels.KeyValueStore, cmp, cmp_data):
    err = False
    for srv in cmp_data["services"]:
        response = requests.delete(url="{}/{}/{}".format(cm_conf.DM.url, cm_conf.DM.api, srv))
        if not response.status_code == 200:
            err = True
            break
    if not err:
        kvs.delete(cmp)
