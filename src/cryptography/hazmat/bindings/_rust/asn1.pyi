import typing

from cryptography.x509 import TLSFeature

class TestCertificate:
    not_after_tag: int
    not_before_tag: int
    issuer_value_tags: typing.List[int]
    subject_value_tags: typing.List[int]

def decode_dss_signature(signature: bytes) -> typing.Tuple[int, int]: ...
def encode_dss_signature(r: int, s: int) -> bytes: ...
def parse_spki_for_data(data: bytes) -> bytes: ...
def test_parse_certificate(data: bytes) -> TestCertificate: ...
