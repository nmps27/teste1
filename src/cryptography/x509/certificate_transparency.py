# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.


import abc
import datetime

from cryptography import utils
from cryptography.hazmat.bindings._rust import x509 as rust_x509


class LogEntryType(utils.Enum):
    X509_CERTIFICATE = 0
    PRE_CERTIFICATE = 1


class Version(utils.Enum):
    v1 = 0


class SignedCertificateTimestamp(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def version(self) -> Version:
        """
        Returns the SCT version.
        """

    @abc.abstractproperty
    def log_id(self) -> bytes:
        """
        Returns an identifier indicating which log this SCT is for.
        """

    @abc.abstractproperty
    def timestamp(self) -> datetime.datetime:
        """
        Returns the timestamp for this SCT.
        """

    @abc.abstractproperty
    def entry_type(self) -> LogEntryType:
        """
        Returns whether this is an SCT for a certificate or pre-certificate.
        """

    @abc.abstractproperty
    def hash_algorithm(self) -> int:
        """
        Returns the hash algorithm used for the SCT's signature.

        See: <https://datatracker.ietf.org/doc/html/rfc5246#section-7.4.1.4.1>
        """

    @abc.abstractproperty
    def signature_algorithm(self) -> int:
        """
        Returns the signing algorithm used for the SCT's signature.

        See: <https://datatracker.ietf.org/doc/html/rfc5246#section-7.4.1.4.1>
        """

    @abc.abstractproperty
    def signature(self) -> bytes:
        """
        Returns the signature for this SCT.
        """


SignedCertificateTimestamp.register(rust_x509.Sct)
