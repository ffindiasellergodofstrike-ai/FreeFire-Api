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
    """Apply PKCS#7 padding to text"""
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)


def unpad(text: bytes) -> bytes:
    """Remove PKCS#7 padding from text"""
    padding_length = text[-1]
    if padding_length < 1 or padding_length > AES.block_size:
        raise ValueError(f"Invalid padding length: {padding_length}")
    return text[:-padding_length]


def aes_cbc_encrypt(text: bytes) -> bytes:
    """Encrypt text using AES CBC mode"""
    aes = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    return aes.encrypt(pad(text))


def aes_cbc_decrypt(ciphertext: bytes) -> bytes:
    """Decrypt ciphertext using AES CBC mode"""
    aes = AES.new(MAIN_KEY, AES.MODE_CBC, MAIN_IV)
    decrypted = aes.decrypt(ciphertext)
    return unpad(decrypted)


def encode_protobuf(data: dict, proto_message: Message) -> bytes:
    """
    Utility function to convert dictionary/data to proto bytes with AES encryption
    
    Args:
        data (dict): Dictionary with proto data
        proto_message (Message): Proto message instance
    
    Returns:
        bytes: AES-encrypted serialized proto data
    
    Raises:
        ValueError: If input is invalid
        Exception: If proto conversion fails
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
    Decode a protobuf message. 
    Smart Detection: OB54 large profiles start with byte 10 (0x0A) and are NOT AES.
    """
    if not encoded_data:
        raise ValueError("encoded_data cannot be empty")
    
    instance = message_type()
    
    # --- SMART DETECTION LOGIC ---
    # 1. Agar pehla byte 10 hai, to wo Protobuf tag (field 1) hai.
    # 2. Agar length 16 ka multiple nahi hai, to wo AES ho hi nahi sakta.
    is_likely_raw = (encoded_data[0] == 10) or (len(encoded_data) % 16 != 0)
    
    if is_likely_raw:
        try:
            # Pehle direct parse karke dekhte hain
            instance.ParseFromString(encoded_data)
            return json.loads(json_format.MessageToJson(instance))
        except Exception:
            # Agar direct fail ho gaya, to niche AES wala logic chalne do
            pass

    # --- AES DECRYPTION ATTEMPT ---
    aes_error = None
    try:
        decrypted = aes_cbc_decrypt(encoded_data)
        instance = message_type()
        instance.ParseFromString(decrypted)
        return json.loads(json_format.MessageToJson(instance))
    except Exception as e:
        aes_error = str(e)
    
    # --- FINAL FALLBACK (RAW PARSING) ---
    try:
        instance = message_type()
        # ignore_unknown_fields logic (OB54 updates ke liye zaroori hai)
        instance.ParseFromString(encoded_data)
        return json.loads(json_format.MessageToJson(instance))
    except Exception as raw_e:
        error_msg = (
            f"Failed to decode. AES Error: {aes_error}. "
            f"Raw Error: {str(raw_e)}. Data len: {len(encoded_data)}"
        )
        raise Exception(error_msg)


def encode_protobuf_raw(data: dict, proto_message: message.Message) -> bytes:
    """
    Encodes to Protobuf WITHOUT AES encryption (Required for game data)
    
    Args:
        data (dict): Dictionary with proto data
        proto_message (message.Message): Proto message instance
    
    Returns:
        bytes: Serialized proto data (unencrypted)
    
    Raises:
        Exception: If proto conversion fails
    """
    try:
        json_format.ParseDict(data, proto_message)
        return proto_message.SerializeToString()
    except Exception as e:
        raise Exception(f"Raw proto conversion failed: {str(e)}")
