# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

from cryptography import utils
from cryptography.hazmat.primitives import interfaces


@utils.register_interface(interfaces.AsymmetricPadding)
class PKCS1(object):
    name = "EMSA-PKCS1-v1_5"


@utils.register_interface(interfaces.AsymmetricPadding)
class PSS(object):
    name = "EMSA-PSS"
