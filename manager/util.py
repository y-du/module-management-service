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


from .configuration import mm_conf, EnvVars
import snorkels
import typing
import json
import requests


__all__ = ("ModuleState", "parseModule", "activateModule", "deactivateModule", "removeModule")


class ModuleState:
    active = "active"
    inactive = "inactive"


def parseModule(module: dict) -> typing.Tuple[dict, dict]:
    m_data = {
        "name": module["name"],
        "description": module["description"],
        "services": {key: {"hash": srv["hash"]} for key, srv in module["services"].items()},
        "hash": module["hash"]
    }
    configs = dict()
    for key, srv in module["services"].items():
        del srv["hash"]
        configs[key] = srv
    return m_data, configs


def activateModule(kvs: snorkels.KeyValueStore, mod: str, configs: dict, m_data):
    err = False
    for srv, config in configs.items():
        config["name"] = srv
        config["runtime_vars"] = {
            EnvVars.ModuleID.name: mod,
            EnvVars.GatewayLocalIP.name: EnvVars.GatewayLocalIP.value
        }
        response = requests.post(url="{}/{}".format(mm_conf.DM.url, mm_conf.DM.api), json=config)
        if not response.status_code == 200:
            err = True
            break
    if not err:
        for srv in configs:
            response = requests.patch(url="{}/{}/{}".format(mm_conf.DM.url, mm_conf.DM.api, srv), json={"state": "running"})
            if not response.status_code == 200:
                err = True
                break
    if not err:
        m_data["state"] = ModuleState.active
        kvs.set(mod, json.dumps(m_data))


def deactivateModule(kvs: snorkels.KeyValueStore, mod: str, m_data):
    err = False
    for srv in m_data["services"]:
        response = requests.patch(url="{}/{}/{}".format(mm_conf.DM.url, mm_conf.DM.api, srv), json={"state": "stopped"})
        if not response.status_code == 200:
            err = True
            break
    if not err:
        for srv in m_data["services"]:
            response = requests.delete(url="{}/{}/{}".format(mm_conf.DM.url, mm_conf.DM.api, srv))
            if not response.status_code == 200:
                err = True
                break
    if not err:
        m_data["state"] = ModuleState.inactive
        kvs.set(mod, json.dumps(m_data))


def removeModule(kvs: snorkels.KeyValueStore, mod, m_data):
    err = False
    for srv in m_data["services"]:
        response = requests.delete(url="{}/{}/{}?option=purge".format(mm_conf.DM.url, mm_conf.DM.api, srv))
        if not response.status_code == 200:
            err = True
            break
    if not err:
        kvs.delete(mod)
