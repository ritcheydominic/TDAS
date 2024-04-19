import base64
import json
import os
from datetime import datetime

import segno
from nacl.encoding import Base64Encoder, HexEncoder
from nacl.signing import SigningKey, VerifyKey
from PIL import Image
from pyzbar.pyzbar import decode

from tdasutils import get_public_key
from timestamputils import timestamp_signature, verify_timestamp


def seal_document(key_file_name, manifest_file_name):
    # Load private (signing) and public (verifying) key data
    key_file = open(key_file_name)
    key_data = json.load(key_file)
    signing_key = SigningKey(key_data["private_key"], encoder=Base64Encoder)
    verify_key_domain_name = key_data["public_key_domain_name"]

    # Load manifest
    manifest_file = open(manifest_file_name)
    manifest_data = json.load(manifest_file)
    manifest = json.dumps(manifest_data)

    # Sign manifest and save for comparison later
    signed_manifest = signing_key.sign(bytes(manifest, 'utf-8'))
    signing_key.verify_key.verify(signed_manifest)

    with open('test_manifest.sig', 'w') as fp:
        fp.write(signed_manifest.decode(errors="ignore"))

    # Generate seal QR code
    seal = dict()
    seal["version"] = 1
    seal["signature"] = signed_manifest.hex()
    seal["public_key_domain_name"] = verify_key_domain_name
    seal_qr_code = segno.make_qr(json.dumps(seal), mode="byte")
    seal_qr_code.save("seal_qr_code.png", border=3, scale=5)

    # Uncomment lines 43 and 46 and comment out line 47 to generate a timestamp file and use that

    # Timestamp manifest
    # timestamp_file_name = timestamp_signature(signed_manifest.decode(errors="ignore"), "timestamp")

    # Generate timestamp
    # timestamp_file = open(timestamp_file_name, mode="rb")
    timestamp_file = open("timestamp.ots", mode="rb")
    timestamp_data = timestamp_file.read()
    timestamp_qr_code = segno.make_qr(timestamp_data, mode="byte")
    timestamp_qr_code.save("timestamp_qr_code.png", border=3, scale=5)

def authenticate_document(seal_qr_code_file_name, timestamp_qr_code_file_name):
    # Decode seal QR code
    seal_qr_code = decode(Image.open(seal_qr_code_file_name))
    seal_data = seal_qr_code[0].data.decode('utf-8')
    seal = json.loads(seal_data)

    # Decode timestamp QR code
    timestamp_qr_code = decode(Image.open(timestamp_qr_code_file_name), binary=True)
    timestamp_data = timestamp_qr_code[0].data

    # Decompose seal and fetch public key
    seal_version = seal["version"]
    signed_manifest = seal["signature"]
    verify_key_domain_name = seal["public_key_domain_name"]
    dns_record_tdas_version, public_key_format, public_key, public_key_begin_date, public_key_expiry_date = get_public_key(verify_key_domain_name)

    # Verify timestamp against blockchain
    timestamp_file = open("temp.ots", "wb")
    timestamp_file.write(timestamp_data)
    timestamp_file.close()
    timestamp_verification_result = verify_timestamp("temp.ots")
    os.remove("temp.ots")
    if timestamp_verification_result is None:
        raise Exception("Timestamp forged or corrupt")
    
    # Verify timestamp against public key validity dates
    timestamp_year, timestamp_month, timestamp_day = timestamp_verification_result.split("-")
    timestamp = datetime(year=timestamp_year, month=timestamp_month, day=timestamp_day, hour=0, minute=0, second=0)
    if timestamp < public_key_begin_date:
        raise Exception("Public key was not yet valid when timestamped")
    elif timestamp > public_key_expiry_date:
        raise Exception("Public key was no longer valid when timestamped")
    
    # Verify manifest signature
    verify_key = VerifyKey(bytes(public_key, 'utf-8'), encoder=Base64Encoder)
    manifest_data = verify_key.verify(bytes(signed_manifest, 'utf-8'), encoder=HexEncoder).decode("utf-8")
    manifest = json.loads(manifest_data)
    
    # Verify manifest contents against document
    print("Document Summary")
    for key in manifest:
        print("{}: {}".format(key, manifest[key]))
    response = input("Does the above information match what is presented on the document? [Y/N] ")
    if response != "Y" and response != "y":
        raise Exception("User verification of manifest failed")
    
    print("Document authenticated!")

def generate_key():
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    signing_key_b64 = signing_key.encode(encoder=Base64Encoder)
    verify_key_b64 = verify_key.encode(encoder=Base64Encoder)

    print(signing_key_b64)
    print(verify_key_b64)

seal_document('test_key_2.json', 'test_manifest.json')
authenticate_document("seal_qr_code.png", "timestamp_qr_code.png")
