# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

from cryptography.hazmat.bindings._crypt32 import ffi, lib


class Binding(object):
    """
    Crypt32 API wrapper.
    """
    lib = lib
    ffi = ffi
