# Copyright 2020 OpenRCA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time

from orca.common import logger
from orca.graph import graph
from orca.topology import probe
from orca import exceptions

log = logger.get_logger(__name__)


class UpstreamProxy(probe.UpstreamProxy):

    def __init__(self, prom_client):
        self._prom_client = prom_client

    def get_all(self):
        return self._prom_client.get_alerts()['data']['alerts']