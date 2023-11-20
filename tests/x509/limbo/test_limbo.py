# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

import datetime
import json
import os
from ipaddress import IPv4Address

from cryptography import x509
from cryptography.x509 import load_pem_x509_certificate
from cryptography.x509.verification import (
    PolicyBuilder,
    Store,
    VerificationError,
)

LIMBO_UNSUPPORTED_FEATURES = {
    # NOTE: Path validation is required to reject wildcards on public suffixes,
    # however this isn't practical and most implementations make no attempt to
    # comply with this.
    "pedantic-public-suffix-wildcard",
    # TODO: We don't support Distinguished Name Constraints yet.
    "name-constraint-dn",
    # Our support for custom EKUs is limited, and we (like most impls.) don't
    # handle all EKU conditions under CABF.
    "pedantic-webpki-eku",
    # Similarly: contains tests that fail based on a strict reading of RFC 5280
    # but are widely ignored by validators.
    "pedantic-rfc5280",
}

LIMBO_XFAIL_TESTCASES = {
    # We currently allow intermediate CAs that don't have AKIs, which
    # is technically forbidden under CABF. This is consistent with what
    # Go's crypto/x509 and Rust's webpki crate do.
    "rfc5280::intermediate-missing-aki",
    # We allow root CAs where the AKI and SKI mismatch, which is technically
    # forbidden under CABF. This is consistent with what
    # Go's crypto/x509 and Rust's webpki crate do.
    "webpki::aki::root-with-aki-ski-mismatch",
}


def _get_limbo_peer(expected_peer):
    assert expected_peer is not None

    kind = expected_peer["kind"]
    assert kind in ("DNS", "IP")
    value = expected_peer["value"]
    if kind == "DNS":
        return x509.DNSName(value)
    else:
        return x509.IPAddress(IPv4Address(value))


def _limbo_testcase(testcase):
    if testcase["id"] in LIMBO_XFAIL_TESTCASES:
        return

    features = testcase["features"]
    if features is not None and LIMBO_UNSUPPORTED_FEATURES.intersection(
        features
    ):
        return
    assert testcase["validation_kind"] == "SERVER"
    assert testcase["signature_algorithms"] is None
    assert testcase["extended_key_usage"] is None or testcase[
        "extended_key_usage"
    ] == ["serverAuth"]
    assert testcase["expected_peer_names"] is None

    trusted_certs = [
        load_pem_x509_certificate(cert.encode())
        for cert in testcase["trusted_certs"]
    ]
    untrusted_intermediates = [
        load_pem_x509_certificate(cert.encode())
        for cert in testcase["untrusted_intermediates"]
    ]
    peer_certificate = load_pem_x509_certificate(
        testcase["peer_certificate"].encode()
    )
    peer_name = _get_limbo_peer(testcase["expected_peer_name"])
    validation_time = testcase["validation_time"]
    validation_time = (
        datetime.datetime.fromisoformat(validation_time)
        if validation_time is not None
        else None
    )
    max_chain_depth = testcase["max_chain_depth"]
    should_pass = testcase["expected_result"] == "SUCCESS"

    verifier = PolicyBuilder(
        time=validation_time,
        store=Store(trusted_certs),
        max_chain_depth=max_chain_depth,
    ).build_server_verifier(peer_name)

    try:
        built_chain = verifier.verify(
            peer_certificate, untrusted_intermediates
        )
        assert should_pass, testcase["id"]

        # Assert that the verifier returns chains in [EE, ..., TA] order.
        assert built_chain[0] == peer_certificate
        assert built_chain[-1] in trusted_certs
    except VerificationError:
        assert not should_pass, testcase["id"]


def test_limbo(subtests, pytestconfig):
    limbo_root = pytestconfig.getoption("--x509-limbo-root", skip=True)
    limbo_path = os.path.join(limbo_root, "limbo.json")
    with open(limbo_path) as limbo_file:
        limbo = json.load(limbo_file)
        testcases = limbo["testcases"]
        for testcase in testcases:
            with subtests.test():
                _limbo_testcase(testcase)
