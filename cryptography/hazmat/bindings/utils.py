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

import binascii
import sys
import threading

from cffi import FFI
from cffi.verifier import Verifier


def build_ffi_for_binding(module_prefix, modules, pre_include="",
                          post_include="", libraries=[], extra_compile_args=[],
                          extra_link_args=[]):
    """
    Modules listed in ``modules`` should have the following attributes:

    * ``INCLUDES``: A string containing C includes.
    * ``TYPES``: A string containing C declarations for types.
    * ``FUNCTIONS``: A string containing C declarations for functions.
    * ``MACROS``: A string containing C declarations for any macros.
    * ``CUSTOMIZATIONS``: A string containing arbitrary top-level C code, this
        can be used to do things like test for a define and provide an
        alternate implementation based on that.
    * ``CONDITIONAL_NAMES``: A dict mapping strings of condition names from the
        library to a list of names which will not be present without the
        condition.
    """
    types = []
    includes = []
    functions = []
    macros = []
    customizations = []
    for name in modules:
        module_name = module_prefix + name
        __import__(module_name)
        module = sys.modules[module_name]

        types.append(module.TYPES)
        macros.append(module.MACROS)
        functions.append(module.FUNCTIONS)
        includes.append(module.INCLUDES)
        customizations.append(module.CUSTOMIZATIONS)

    # We include functions here so that if we got any of their definitions
    # wrong, the underlying C compiler will explode. In C you are allowed
    # to re-declare a function if it has the same signature. That is:
    #   int foo(int);
    #   int foo(int);
    # is legal, but the following will fail to compile:
    #   int foo(int);
    #   int foo(short);
    verify_source = "\n".join(
        [pre_include] +
        includes +
        [post_include] +
        functions +
        customizations
    )
    ffi, lib = build_ffi(
        cdef_source="\n".join(types + functions + macros),
        verify_source=verify_source,
        libraries=libraries,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )

    for name in modules:
        module_name = module_prefix + name
        module = sys.modules[module_name]
        for condition, names in module.CONDITIONAL_NAMES.items():
            if not getattr(lib, condition):
                for name in names:
                    delattr(lib, name)

    return ffi, lib


class LazyLibrary(object):
    def __init__(self, verifier):
        self._lock = threading.Lock()
        self._verifier = verifier
        self._lib = None

    def __getattr__(self, name):
        if self._lib is None:
            with self._lock:
                if self._lib is None:
                    self._lib = self._verifier.load_library()
        return getattr(self._lib, name)


def _compile_module(*args, **kwargs):
    raise RuntimeError(
        "Attempted implicit compile of a cffi module. All cffi modules should "
        "be pre-compiled at installation time."
    )

def build_ffi(cdef_source, verify_source, libraries=[], extra_compile_args=[],
              extra_link_args=[]):
    ffi = FFI()
    ffi.cdef(cdef_source)

    ffi.verifier = Verifier(
        ffi,
        verify_source,
        tmpdir='',
        modulename=_create_modulename(cdef_source, verify_source, sys.version),
        libraries=libraries,
        ext_package="cryptography",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
    ffi.verifier.compile_module = _compile_module
    ffi.verifier._compile_module = _compile_module
    return ffi, LazyLibrary(ffi.verifier)


def _create_modulename(cdef_sources, source, sys_version):
    """
    cffi creates a modulename internally that incorporates the cffi version.
    This will cause cryptography's wheels to break when the version of cffi
    the user has does not match what was used when building the wheel. To
    resolve this we build our own modulename that uses most of the same code
    from cffi but elides the version key.
    """
    key = '\x00'.join([sys_version[:3], source, cdef_sources])
    key = key.encode('utf-8')
    k1 = hex(binascii.crc32(key[0::2]) & 0xffffffff)
    k1 = k1.lstrip('0x').rstrip('L')
    k2 = hex(binascii.crc32(key[1::2]) & 0xffffffff)
    k2 = k2.lstrip('0').rstrip('L')
    return '_Cryptography_cffi_{0}{1}'.format(k1, k2)
