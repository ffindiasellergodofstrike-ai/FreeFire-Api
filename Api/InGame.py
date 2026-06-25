import requests
import json
import Proto.compiled.PlayerPersonalShow_pb2
import Proto.compiled.PlayerStats_pb2
import Proto.compiled.PlayerCSStats_pb2
import Proto.compiled.SearchAccountByName_pb2
from Utilities.until import encode_protobuf, decode_protobuf
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG

# --- Helper: Safe JSON decoder ---
def safe_json_load(data):
    try:
        return json.loads(json.dumps(data, default=str))
    except:
        return {}

def search_account_by_keyword(server_url, auth_token, keyword):
    try:
        endpoint = f"{server_url}/FuzzySearchAccountByName"
        payload = encode_protobuf(
            {"keyword": str(keyword)},
            Proto.compiled.SearchAccountByName_pb2.request()
        )

        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Expect": "100-continue",
            "Authorization": f"Bearer {auth_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": RELEASEVERSION,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = requests.post(endpoint, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        if DEBUG:
            print("[I] RES:", response.content, "\n")

        decoded = decode_protobuf(
            response.content,
            Proto.compiled.SearchAccountByName_pb2.response
        )
        return safe_json_load(decoded)

    except Exception as e:
        raise RuntimeError(f"Unhandled error in search_account_by_keyword: {e}")

def get_player_personal_show(serverurl, authorization, account_id, need_gallery_info=False, call_sign_src=7, need_blacklist=False, need_spark_info=False):
    # Setup Payload
    payload_data = {
        "accountId": account_id,
        "callSignSrc": call_sign_src,
        "needGalleryInfo": need_gallery_info,
        "needBlacklist": need_blacklist,
        "needSparkInfo": need_spark_info,
    }
    encrypted_payload = encode_protobuf(payload_data, Proto.compiled.PlayerPersonalShow_pb2.request())

    # Setup Headers
    headers = {
        "Host": "client.ind.freefiremobile.com",
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Authorization": f"Bearer {authorization}",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2022.3.47f1",
        "Content-Length": "16"
    }

    url = f"{serverurl}/GetPlayerPersonalShow"
    
    try:
        response = requests.post(url, data=encrypted_payload, headers=headers)
        response.raise_for_status()
        
        # Normal Decoding
        message = decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)
        return safe_json_load(message)
        
    except Exception as e:
        # Crash bypass: Instead of crashing, return a status error
        print(f"[!] Critical Parsing Error in get_player_personal_show: {e}")
        return {"status": "error", "message": "Schema update required", "error_details": str(e)}

def get_player_stats(authorization, serverurl, mode, uid, match_type="CAREER"):
    try:
        # Input Validation
        if not str(uid).isdigit():
            raise ValueError(f"Invalid UID: {uid}")
        
        uid = int(uid)
        mode = mode.lower()
        match_type = match_type.upper()
        
        # Configuration based on Mode
        if mode == "br":
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 2}
            url = f"{serverurl}/GetPlayerStats"
            proto_module = Proto.compiled.PlayerStats_pb2
        else: # cs mode
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 6}
            url = f"{serverurl}/GetPlayerTCStats"
            proto_module = Proto.compiled.PlayerCSStats_pb2
        
        matchmode = type_mapping.get(match_type, 0)
        
        payload_data = {"accountid": uid, "matchmode": matchmode}
        if mode == "cs": 
            payload_data["gamemode"] = 15
            
        encrypted_payload = encode_protobuf(payload_data, proto_module.request())
        
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            'Authorization': f"Bearer {authorization}",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/x-www-form-urlencoded"
        }
        
        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        message = decode_protobuf(response.content, proto_module.response)
        return safe_json_load(message)
        
    except Exception as e:
        print(f"[!] Error in get_player_stats: {e}")
        return {"status": "error", "message": str(e)}

# --- Add any other utility functions that were in your file here ---
