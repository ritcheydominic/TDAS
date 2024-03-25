import dns.resolver
from datetime import datetime

def get_public_key(key_domain_name: str):
    dns_answers = dns.resolver.resolve(key_domain_name, "TXT").rrset

    if len(dns_answers) > 1:
        raise Exception("DNS query for key returned more than 1 record")
    
    txt_record = dns_answers[0].to_text()
    
    # Clean up string for processing
    txt_record = txt_record.replace("\"", "") # Get rid of double quotes
    txt_record = txt_record.replace(" ", "")  # Remove spaces

    version = None
    key_format = None
    public_key = ""
    begin_date = None
    expiry_date = None

    # Parse properties in DNS record
    properties = txt_record.split(";")
    for p in properties:
        entries = p.split("=")
        if entries[0] == "":
            continue
        elif entries[0] == "k": # Public key property requires special handling due to possibility of other ='s in string
            for i in range(1, len(entries)):
                public_key += entries[i]
            continue
        elif len(entries) != 2:
            raise Exception("Invalid property in DNS record")
        key, value = entries

        if key == "v":
            value = int(value.replace("TDAS", ""))
            if value != 1:
                raise Exception("DNS record has incompatible TDAS version")
            version = value
        elif key == "f":
            if value != "ed25519":
                raise Exception("Unknown key type in DNS record")
            key_format = value
        elif key == "b":
            begin_date = datetime.fromtimestamp(int(value))
        elif key == "e":
            expiry_date = datetime.fromtimestamp(int(value))
        else:
            raise Exception("Unknown property in DNS record")
    
    if version == None or key_format == None or public_key == "" or begin_date == None or expiry_date == None:
        raise Exception("Required properties not all specified in DNS record")
    
    if begin_date >= expiry_date:
        raise Exception("Invalid key begin/expiry dates")
    
    return (version, key_format, public_key, begin_date, expiry_date)