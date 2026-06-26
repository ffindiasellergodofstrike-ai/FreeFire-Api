import json
from google.protobuf.message import Message
from google.protobuf import json_format, message
from Crypto.Cipher import AES
from Configuration.AESConfiguration import MAIN_KEY, MAIN_IV

# Load accounts from JSON file
def load_accounts():
    try:
        with open('./Configuration/AccountConfiguration.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("AccountConfiguration.json file not found")
    except json.JSONDecodeError:
        raise Exception("Error parsing AccountConfiguration.json")


def pad(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)


def aes_cbc_encrypt(text: bytes) -> bytes:
    aes = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    return aes.encrypt(pad(text))
    

def encode_protobuf(data: dict, proto_message: Message) -> bytes:
    """
    Utility function to convert dictionary/data to proto bytes (AES-encrypted)
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    if not isinstance(proto_message, Message):
        raise ValueError("proto_message must be a protobuf Message")

    try:
        json_format.ParseDict(data, proto_message)
        return aes_cbc_encrypt(proto_message.SerializeToString())
    except Exception as e:
        raise Exception(f"Proto conversion failed: {str(e)}")


def decode_protobuf(encoded_data: bytes, message_type: message.Message) -> dict:
    """
    Decode a protobuf message from AES-encrypted or raw protobuf bytes.
    Returns a Python dict (JSON-serializable).
    """
    def aes_cbc_decrypt(ciphertext: bytes) -> bytes:
        aes = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
        decrypted = aes.decrypt(ciphertext)
        # Remove PKCS#7 padding
        # Python 3: decrypted[-1] is int
        pad_len = decrypted[-1]
        if pad_len < 1 or pad_len > AES.block_size:
            raise ValueError("Invalid padding length")
        return decrypted[:-pad_len]

    try:
        # Try AES decrypt first (most login/endpoints reply with AES)
        try:
            decrypted = aes_cbc_decrypt(encoded_data)
            instance = message_type()
            instance.ParseFromString(decrypted)
        except Exception:
            # If AES-decrypt or parse fails, try raw parse
            instance = message_type()
            instance.ParseFromString(encoded_data)

        # Convert to Python dict via JSON roundtrip (existing behavior)
        return json.loads(json_format.MessageToJson(instance))
    except Exception as e:
        print(f"Protobuf Parsing Error: {e}")
        raise


def encode_protobuf_raw(data: dict, proto_message: message.Message) -> bytes:
    """Encodes to Protobuf WITHOUT AES encryption (Required for some game data)"""
    try:
        json_format.ParseDict(data, proto_message)
        return proto_message.SerializeToString()
    except Exception as e:
        raise Exception(f"Raw Proto conversion failed: {str(e)}")

# Keep your existing encode_protobuf (with AES) for Login functions only
