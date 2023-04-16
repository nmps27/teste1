use crate::{common, extensions, name};
use asn1;

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct TBSRequest<'a> {
    #[explicit(0)]
    #[default(0)]
    pub version: u8,
    #[explicit(1)]
    pub requestor_name: Option<name::GeneralName<'a>>,
    pub request_list: common::Asn1ReadableOrWritable<
        'a,
        asn1::SequenceOf<'a, Request<'a>>,
        asn1::SequenceOfWriter<'a, Request<'a>>,
    >,
    #[explicit(2)]
    pub request_extensions: Option<extensions::Extensions<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct Request<'a> {
    pub req_cert: CertID<'a>,
    #[explicit(0)]
    pub single_request_extensions: Option<extensions::Extensions<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct CertID<'a> {
    pub hash_algorithm: common::AlgorithmIdentifier<'a>,
    pub issuer_name_hash: &'a [u8],
    pub issuer_key_hash: &'a [u8],
    pub serial_number: asn1::BigInt<'a>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct OCSPRequest<'a> {
    pub tbs_request: TBSRequest<'a>,
    // Parsing out the full structure, which includes the entirety of a
    // certificate is more trouble than it's worth, since it's not in the
    // Python API.
    #[explicit(0)]
    pub optional_signature: Option<asn1::Sequence<'a>>,
}
