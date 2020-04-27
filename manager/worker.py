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

__all__ = ("WorkerManager", "WorkerExistsError")


from .logger import getLogger
import threading
import typing


logger = getLogger(__name__.split(".", 1)[-1])


class WorkerExistsError(Exception):
    pass


class Worker(threading.Thread):
    def __init__(self, name, s_clbk, d_clbk):
        super().__init__(name=name, daemon=True)
        self.__task = None
        self.__kwargs = None
        self.__s_clbk = s_clbk
        self.__d_clbk = d_clbk

    def setTask(self, task: typing.Callable, **kwargs):
        self.__task = task
        self.__kwargs = kwargs

    def run(self) -> None:
        self.__s_clbk(self.name)
        logger.debug("starting '{}' ...".format(self.name))
        try:
            self.__task(**self.__kwargs)
        except Exception as ex:
            logger.error("exception in '{}' - {}".format(self.name, ex))
        self.__d_clbk(self.name)
        logger.debug("'{}' finished".format(self.name))


class WorkerManager:
    def __init__(self):
        self.__pool = list()

    def __s_clbk(self, name):
        self.__pool.append(name)

    def __d_clbk(self, name):
        self.__pool.remove(name)

    def getWorker(self, cmp_name: str) -> Worker:
        name = "worker-{}".format(cmp_name)
        if name in self.__pool:
            raise WorkerExistsError("a task is still being executed by '{}'".format(name))
        return Worker(name, self.__s_clbk, self.__d_clbk)
