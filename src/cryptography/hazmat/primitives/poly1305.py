# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function


from cryptography import utils
from cryptography.exceptions import (
    AlreadyFinalized, UnsupportedAlgorithm, _Reasons
)


class Poly1305(object):
    def __init__(self, key):
        from cryptography.hazmat.backends.openssl.backend import backend
        if not backend.poly1305_supported():
            raise UnsupportedAlgorithm(
                "poly1305 is not supported by this version of OpenSSL.",
                _Reasons.UNSUPPORTED_MAC
            )
        self._ctx = backend.create_poly1305_ctx(key)

    def update(self, data):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized.")
        utils._check_byteslike("data", data)
        self._ctx.update(data)

    def finalize(self):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized.")
        mac = self._ctx.finalize()
        self._ctx = None
        return mac

    def verify(self, signature):
        utils._check_bytes("signature", signature)
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized.")

        ctx, self._ctx = self._ctx, None
        ctx.verify(signature)
