# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

import abc


# This exists to break an import cycle. It is normally accessible from the
# ciphers module.


class AsymmetricPadding(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def name(self) -> str:
        """
        A string naming this padding (e.g. "PSS", "PKCS1").
        """
