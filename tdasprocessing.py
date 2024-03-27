import base64
import time
import zlib
import json
import brotli
import qrcode
from PyPDF2 import PdfReader, PdfWriter, Transformation
from io import BytesIO
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate

def sign_string_with_current_timestamp(string_to_sign, private_key_path):
    timestamp = str(int(time.time()))
    return sign_string_with_timestamp(string_to_sign, timestamp, private_key_path)

def sign_string_with_timestamp(string_to_sign, timestamp, private_key_path):
    with open(private_key_path, "rb") as key_file:
        private_key_data = key_file.read()
        private_key = load_pem_private_key(private_key_data, password=None, backend=default_backend())

    timestamp = str(int(time.time()))

    # Concatenate timestamp and string to sign
    timestamped_data = string_to_sign + '|' + timestamp
    data_bytes = timestamped_data.encode('utf-8')

    # openssl dgst -sha256 -sign <private key> -sigopt rsa_padding_mode:pss -out signature.bin data_to_sign.bin
    signature = private_key.sign(
        data_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    signature_b64 = base_encoding['encode'](signature).decode('utf-8')
    return timestamp, timestamped_data, signature_b64

def verify_signature(string_to_verify, signature, cert_path):
    with open(cert_path, "rb") as key_file:
        public_key_data = key_file.read()
        public_key = load_pem_x509_certificate(public_key_data, backend=default_backend()).public_key()

    data_bytes = string_to_verify.encode('utf-8')
    try:
        # Verify the signature
        # openssl dgst -sha256 -verify <public key> -sigopt rsa_padding_mode:pss -signature signature.bin data_to_sign.bin
        public_key.verify(
            signature,
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print("Signature verification failed: ", str(e))
        return False

# Compress (deflate)
def deflate(input_bytes):
    compressed_data = zlib.compress(input_bytes)
    return compressed_data

def inflate(compressed_data):
    decompressed_bytes = zlib.decompress(compressed_data)
    return decompressed_bytes

# Compress (Brotli)
def brotli_compress(data):
    compressed_data = brotli.compress(data)
    return compressed_data

def brotli_decompress(compressed_data):
    decompressed_bytes = brotli.decompress(compressed_data)
    return decompressed_bytes

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    return qr_img

def add_qr_code_to_pdf(image_data, pdf_path, output_path):
    # Open the existing PDF
    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PdfReader(pdf_file)
        pdf_writer = PdfWriter()


        img_io = BytesIO()
        image_data.save(img_io, 'PDF')
        img_io.seek(0)
        img_pdf = PdfReader(img_io)
        image_page = img_pdf.pages[0]
        op = Transformation().scale(sx=QR_CODE_SCALE, sy=QR_CODE_SCALE)
        image_page.add_transformation(op)

        first_page = pdf_reader.pages[0]
        first_page.merge_page(image_page)
        pdf_writer.add_page(first_page)

        # Add other pages
        for page in pdf_reader.pages[1: ]:
            pdf_writer.add_page(page)

        # Write the new PDF to disk
        with open(output_path, "wb") as output_file:
            pdf_writer.write(output_file)

if __name__ == '__main__':
    # Configs
    QR_CODE_SCALE = 0.1
    # base_encoding = {'encode': base64.b64encode, 'decode': base64.b64decode}
    base_encoding = {'encode': base64.b85encode, 'decode': base64.b85decode}
    # compression = {'compress': deflate, 'decompress': inflate}
    compression = {'compress': brotli_compress, 'decompress': brotli_decompress}
    private_key_path = "../ssl/server_privkey.pem"
    cert_path = "../ssl/server_cert.pem"

    # Data
    pdf_path = "../sample.pdf"
    pdf_out_path = "attached.pdf"
    # Essential content is signed
    essential_content = {'FirstName': 'John', 'LastName': 'Doe', 'DoB': '01/01/2024'}
    # Metadata is not signed
    metadata = {'comment': 'Birth certificate', 'correctness': 1, 'version': 1, 'signed': True, 'collection': 'docs', 'node': 'ethereum'}

    # Test sign
    timestamp, timestamped_content, signature_b64 = sign_string_with_current_timestamp(json.dumps(essential_content, sort_keys=True), private_key_path)
    metadata['time'] = timestamp
    metadata['signature'] = signature_b64
    data = json.dumps(metadata, sort_keys=True).encode('utf-8')

    # Test compress
    compressed_data = compression['compress'](data)
    # print(f'Length compressed from {len(data)} to {len(compressed_data)}')

    qr_code_image = generate_qr_code(compressed_data)
    # from PIL import Image
    # qr_code_img.show()

    add_qr_code_to_pdf(qr_code_image, pdf_path, pdf_out_path)

    # Test decompress
    data = compression['decompress'](compressed_data)

    # Test verify
    signature_b64 = json.loads(data)['signature']
    signature = base_encoding['decode'](signature_b64.encode('utf-8'))
    verification_result = verify_signature(timestamped_content, signature, cert_path)
    print("Signature verification result: ", verification_result)