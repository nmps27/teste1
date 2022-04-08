# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.


import binascii

import pytest

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .utils import wycheproof_tests


_DIGESTS = {
    "SHA-1": hashes.SHA1(),
    "SHA-224": hashes.SHA224(),
    "SHA-256": hashes.SHA256(),
    "SHA-384": hashes.SHA384(),
    "SHA-512": hashes.SHA512(),
    # Not supported by OpenSSL for RSA signing
    "SHA-512/224": None,
    "SHA-512/256": None,
    "SHA3-224": hashes.SHA3_224(),
    "SHA3-256": hashes.SHA3_256(),
    "SHA3-384": hashes.SHA3_384(),
    "SHA3-512": hashes.SHA3_512(),
}


def should_verify(backend, wycheproof):
    if wycheproof.valid:
        return True

    if wycheproof.acceptable:
        return not wycheproof.has_flag("MissingNull")

    return False


@wycheproof_tests(
    "rsa_signature_test.json",
    "rsa_signature_2048_sha224_test.json",
    "rsa_signature_2048_sha256_test.json",
    "rsa_signature_2048_sha384_test.json",
    "rsa_signature_2048_sha512_test.json",
    "rsa_signature_2048_sha512_224_test.json",
    "rsa_signature_2048_sha512_256_test.json",
    "rsa_signature_2048_sha3_224_test.json",
    "rsa_signature_2048_sha3_256_test.json",
    "rsa_signature_2048_sha3_384_test.json",
    "rsa_signature_2048_sha3_512_test.json",
    "rsa_signature_3072_sha256_test.json",
    "rsa_signature_3072_sha384_test.json",
    "rsa_signature_3072_sha512_test.json",
    "rsa_signature_3072_sha512_256_test.json",
    "rsa_signature_3072_sha3_256_test.json",
    "rsa_signature_3072_sha3_384_test.json",
    "rsa_signature_3072_sha3_512_test.json",
    "rsa_signature_4096_sha384_test.json",
    "rsa_signature_4096_sha512_test.json",
    "rsa_signature_4096_sha512_256_test.json",
)
def test_rsa_pkcs1v15_signature(backend, wycheproof):
    key = serialization.load_der_public_key(
        binascii.unhexlify(wycheproof.testgroup["keyDer"]), backend
    )
    assert isinstance(key, rsa.RSAPublicKey)
    digest = _DIGESTS[wycheproof.testgroup["sha"]]

    if digest is None or not backend.hash_supported(digest):
        pytest.skip(
            "Hash {} not supported".format(wycheproof.testgroup["sha"])
        )

    if should_verify(backend, wycheproof):
        key.verify(
            binascii.unhexlify(wycheproof.testcase["sig"]),
            binascii.unhexlify(wycheproof.testcase["msg"]),
            padding.PKCS1v15(),
            digest,
        )
    else:
        with pytest.raises(InvalidSignature):
            key.verify(
                binascii.unhexlify(wycheproof.testcase["sig"]),
                binascii.unhexlify(wycheproof.testcase["msg"]),
                padding.PKCS1v15(),
                digest,
            )


@wycheproof_tests("rsa_sig_gen_misc_test.json")
def test_rsa_pkcs1v15_signature_generation(backend, wycheproof):
    key = serialization.load_pem_private_key(
        wycheproof.testgroup["privateKeyPem"].encode(),
        password=None,
        backend=backend,
    )
    assert isinstance(key, rsa.RSAPrivateKey)
    digest = _DIGESTS[wycheproof.testgroup["sha"]]
    assert digest is not None
    if backend._fips_enabled:
        if key.key_size < 2048 or isinstance(digest, hashes.SHA1):
            pytest.skip(
                "Invalid params for FIPS. key: {} bits, digest: {}".format(
                    key.key_size, digest.name
                )
            )

    sig = key.sign(
        binascii.unhexlify(wycheproof.testcase["msg"]),
        padding.PKCS1v15(),
        digest,
    )
    assert sig == binascii.unhexlify(wycheproof.testcase["sig"])


@wycheproof_tests(
    "rsa_pss_2048_sha1_mgf1_20_test.json",
    "rsa_pss_2048_sha256_mgf1_0_test.json",
    "rsa_pss_2048_sha256_mgf1_32_test.json",
    "rsa_pss_2048_sha512_256_mgf1_28_test.json",
    "rsa_pss_2048_sha512_256_mgf1_32_test.json",
    "rsa_pss_3072_sha256_mgf1_32_test.json",
    "rsa_pss_4096_sha256_mgf1_32_test.json",
    "rsa_pss_4096_sha512_mgf1_32_test.json",
    "rsa_pss_misc_test.json",
)
def test_rsa_pss_signature(backend, wycheproof):
    key = serialization.load_der_public_key(
        binascii.unhexlify(wycheproof.testgroup["keyDer"]), backend
    )
    assert isinstance(key, rsa.RSAPublicKey)
    digest = _DIGESTS[wycheproof.testgroup["sha"]]
    mgf_digest = _DIGESTS[wycheproof.testgroup["mgfSha"]]

    if digest is None or mgf_digest is None:
        pytest.skip(
            "PSS with digest={} and MGF digest={} not supported".format(
                wycheproof.testgroup["sha"],
                wycheproof.testgroup["mgfSha"],
            )
        )

    padding_opt = padding.PSS(
        mgf=padding.MGF1(mgf_digest),
        salt_length=wycheproof.testgroup["sLen"],
    )

    if not backend.rsa_padding_supported(
        padding_opt
    ) or not backend.signature_hash_supported(digest):
        pytest.skip(
            f"RSA with padding={padding_opt} and digest={digest} not supported"
        )

    if wycheproof.valid or wycheproof.acceptable:
        key.verify(
            binascii.unhexlify(wycheproof.testcase["sig"]),
            binascii.unhexlify(wycheproof.testcase["msg"]),
            padding_opt,
            digest,
        )
    else:
        with pytest.raises(InvalidSignature):
            key.verify(
                binascii.unhexlify(wycheproof.testcase["sig"]),
                binascii.unhexlify(wycheproof.testcase["msg"]),
                padding_opt,
                digest,
            )


@wycheproof_tests(
    "rsa_oaep_2048_sha1_mgf1sha1_test.json",
    "rsa_oaep_2048_sha224_mgf1sha1_test.json",
    "rsa_oaep_2048_sha224_mgf1sha224_test.json",
    "rsa_oaep_2048_sha256_mgf1sha1_test.json",
    "rsa_oaep_2048_sha256_mgf1sha256_test.json",
    "rsa_oaep_2048_sha384_mgf1sha1_test.json",
    "rsa_oaep_2048_sha384_mgf1sha384_test.json",
    "rsa_oaep_2048_sha512_mgf1sha1_test.json",
    "rsa_oaep_2048_sha512_mgf1sha512_test.json",
    "rsa_oaep_3072_sha256_mgf1sha1_test.json",
    "rsa_oaep_3072_sha256_mgf1sha256_test.json",
    "rsa_oaep_3072_sha512_mgf1sha1_test.json",
    "rsa_oaep_3072_sha512_mgf1sha512_test.json",
    "rsa_oaep_4096_sha256_mgf1sha1_test.json",
    "rsa_oaep_4096_sha256_mgf1sha256_test.json",
    "rsa_oaep_4096_sha512_mgf1sha1_test.json",
    "rsa_oaep_4096_sha512_mgf1sha512_test.json",
    "rsa_oaep_misc_test.json",
)
def test_rsa_oaep_encryption(backend, wycheproof):
    key = serialization.load_pem_private_key(
        wycheproof.testgroup["privateKeyPem"].encode("ascii"),
        password=None,
        backend=backend,
    )
    assert isinstance(key, rsa.RSAPrivateKey)
    digest = _DIGESTS[wycheproof.testgroup["sha"]]
    mgf_digest = _DIGESTS[wycheproof.testgroup["mgfSha"]]
    assert digest is not None
    assert mgf_digest is not None

    padding_algo = padding.OAEP(
        mgf=padding.MGF1(algorithm=mgf_digest),
        algorithm=digest,
        label=binascii.unhexlify(wycheproof.testcase["label"]),
    )

    if wycheproof.valid or wycheproof.acceptable:
        pt = key.decrypt(
            binascii.unhexlify(wycheproof.testcase["ct"]), padding_algo
        )
        assert pt == binascii.unhexlify(wycheproof.testcase["msg"])
    else:
        with pytest.raises(ValueError):
            key.decrypt(
                binascii.unhexlify(wycheproof.testcase["ct"]), padding_algo
            )


@wycheproof_tests(
    "rsa_pkcs1_2048_test.json",
    "rsa_pkcs1_3072_test.json",
    "rsa_pkcs1_4096_test.json",
)
def test_rsa_pkcs1_encryption(backend, wycheproof):
    key = serialization.load_pem_private_key(
        wycheproof.testgroup["privateKeyPem"].encode("ascii"),
        password=None,
        backend=backend,
    )
    assert isinstance(key, rsa.RSAPrivateKey)

    if wycheproof.valid:
        pt = key.decrypt(
            binascii.unhexlify(wycheproof.testcase["ct"]), padding.PKCS1v15()
        )
        assert pt == binascii.unhexlify(wycheproof.testcase["msg"])
    else:
        with pytest.raises(ValueError):
            key.decrypt(
                binascii.unhexlify(wycheproof.testcase["ct"]),
                padding.PKCS1v15(),
            )
