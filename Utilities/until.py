import json
from google.protobuf.message import Message
from google.protobuf import json_format, message
from Crypto.Cipher import AES
from Configuration.AESConfiguration import MAIN_KEY, MAIN_IV

# Load accounts from JSON file (UNTOUCHED)
def load_accounts():
    try:
        with open('./Configuration/AccountConfiguration.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("AccountConfiguration.json file not found")
    except json.JSONDecodeError:
        raise Exception("Error parsing AccountConfiguration.json")


def pad(text: bytes) -> bytes:
    """Apply PKCS#7 padding to text (UNTOUCHED)"""
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)


def unpad(text: bytes) -> bytes:
    """Remove PKCS#7 padding from text (UNTOUCHED)"""
    padding_length = text[-1]
    if padding_length < 1 or padding_length > AES.block_size:
        raise ValueError(f"Invalid padding length: {padding_length}")
    return text[:-padding_length]


def aes_cbc_encrypt(text: bytes) -> bytes:
    """Encrypt text using AES CBC mode (UNTOUCHED)"""
    aes = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    return aes.encrypt(pad(text))


def aes_cbc_decrypt(ciphertext: bytes) -> bytes:
    """Decrypt ciphertext using AES CBC mode (UNTOUCHED)"""
    aes = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    decrypted = aes.decrypt(ciphertext)
    return unpad(decrypted)


def encode_protobuf(data: dict, proto_message: Message) -> bytes:
    """
    Utility function to convert dictionary/data to proto bytes with AES encryption (UNTOUCHED)
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    if not isinstance(proto_message, Message):
        raise ValueError("proto_message must be a protobuf Message")
    
    try:
        json_format.ParseDict(data, proto_message)
        serialized = proto_message.SerializeToString()
        return aes_cbc_encrypt(serialized)
    except Exception as e:
        raise Exception(f"Proto encoding failed: {str(e)}")


def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> dict:
    """
    REFINED FOR OB54: Smart detection for AES vs RAW protobuf.
    Uses MergeFromString for maximum compatibility with large profiles.
    """
    if not encoded_data:
        raise ValueError("encoded_data cannot be empty")
    
    # 1. AES CANDIDATE CHECK
    # AES data must be a multiple of 16. If not, it's definitely raw.
    is_aes_candidate = (len(encoded_data) % 16 == 0)
    aes_error = None

    if is_aes_candidate:
        try:
            # Try AES Decryption
            decrypted = aes_cbc_decrypt(encoded_data)
            instance = message_type()
            # MergeFromString is safer for reverse engineering
            instance.MergeFromString(decrypted)
            return json.loads(json_format.MessageToJson(instance))
        except Exception as e:
            aes_error = str(e)

    # 2. RAW PROTOBUF FALLBACK
    # If not AES or AES failed, try parsing as raw.
    try:
        instance = message_type()
        
        # Automatic Garena Header detection (Sometimes first 5 bytes are header)
        data_to_parse = encoded_data
        if len(encoded_data) > 5 and encoded_data[0] != 10 and encoded_data[5] == 10:
            data_to_parse = encoded_data[5:]
        
        instance.MergeFromString(data_to_parse)
        return json.loads(json_format.MessageToJson(instance))
    
    except Exception as raw_e:
        error_msg = (
            f"Failed to decode protobuf message of type '{message_type.DESCRIPTOR.name}'. "
            f"AES attempt: {aes_error}. Raw attempt: {str(raw_e)}. "
            f"Data length: {len(encoded_data)} bytes."
        )
        raise Exception(error_msg)


def encode_protobuf_raw(data: dict, proto_message: message.Message) -> bytes:
    """
    Encodes to Protobuf WITHOUT AES encryption (UNTOUCHED)
    """
    try:
        json_format.ParseDict(data, proto_message)
        return proto_message.SerializeToString()
    except Exception as e:
        raise Exception(f"Raw proto conversion failed: {str(e)}")
