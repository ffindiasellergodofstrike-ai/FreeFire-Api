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


def decode_protobuf(encoded_data: bytes, message_type):
    if not encoded_data:
        return {}

    instance = message_type()
    
    # 1. Smart Check: MajorLogin (8) or PlayerInfo (10)
    # Agar data raw hai to direct parse karo
    first_byte = encoded_data[0]
    if first_byte in [8, 10] or len(encoded_data) % 16 != 0:
        try:
            instance.MergeFromString(encoded_data)
            return json_format.MessageToDict(instance, preserving_proto_field_name=True)
        except:
            pass

    # 2. AES Decryption Attempt
    if len(encoded_data) % 16 == 0:
        try:
            cipher = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
            decrypted = cipher.decrypt(encoded_data)
            # PKCS7 Unpadding
            padding_len = decrypted[-1]
            if padding_len < 16:
                decrypted = decrypted[:-padding_len]
            
            new_instance = message_type()
            new_instance.MergeFromString(decrypted)
            return json_format.MessageToDict(new_instance, preserving_proto_field_name=True)
        except:
            pass

    # 3. Last Resort: Skip 1st byte (Garena Status Byte)
    try:
        final_instance = message_type()
        final_instance.MergeFromString(encoded_data[1:])
        return json_format.MessageToDict(final_instance, preserving_proto_field_name=True)
    except:
        return {} # Empty dict return karo crash se bachne ke liye


def encode_protobuf_raw(data: dict, proto_message: message.Message) -> bytes:
    """
    Encodes to Protobuf WITHOUT AES encryption (UNTOUCHED)
    """
    try:
        json_format.ParseDict(data, proto_message)
        return proto_message.SerializeToString()
    except Exception as e:
        raise Exception(f"Raw proto conversion failed: {str(e)}")
