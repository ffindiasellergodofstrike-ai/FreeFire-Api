import requests
import json
import traceback
from flask import Flask, request, jsonify

# Proto Imports
import Proto.compiled.PlayerPersonalShow_pb2
import Proto.compiled.PlayerStats_pb2
import Proto.compiled.PlayerCSStats_pb2
import Proto.compiled.SearchAccountByName_pb2
from Utilities.until import encode_protobuf, decode_protobuf
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG

def get_standard_headers(auth_token):
    """Cleaned headers for OB54 compatibility"""
    return {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {auth_token}",
        "X-Unity-Version": "2022.3.47f1",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
    }

def get_player_personal_show(serverurl, authorization, account_id, need_gallery_info=False, call_sign_src=7, need_blacklist=False, need_spark_info=False):
    """
    Fixed Version: Accepts 7 arguments to match your caller.
    """
    # Fix 404: Remove trailing slashes
    url = f"{serverurl.rstrip('/')}/GetPlayerPersonalShow"

    try:
        # Prepare the payload with the arguments provided
        payload_data = {
            "accountId": int(account_id),
            "callSignSrc": int(call_sign_src),
            "needGalleryInfo": bool(need_gallery_info),
            "needBlacklist": bool(need_blacklist),
            "needSparkInfo": bool(need_spark_info),
        }
        
        # Encode payload to Protobuf
        encrypted_payload = encode_protobuf(payload_data, Proto.compiled.PlayerPersonalShow_pb2.request())
        
        # Get cleaned headers (Fix 404/Parsing: No manual Content-Length)
        headers = get_standard_headers(authorization)
        
        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=15)
        
        if DEBUG:
            print(f"[DEBUG] PersonalShow URL: {url}")
            print(f"[DEBUG] Raw Response: {response.content[:50]}...")
            
        response.raise_for_status()
        
        # Decode protobuf response
        message = decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)
        
        # Convert to JSON serializable dict
        return json.loads(json.dumps(message, default=str))
        
    except Exception as e:
        print(f"Error in get_player_personal_show: {e}")
        traceback.print_exc() # This will show you exactly if OB54 fields are missing
        return None

def search_account_by_keyword(server_url, auth_token, keyword):
    try:
        endpoint = f"{server_url.rstrip('/')}/FuzzySearchAccountByName"
        payload = encode_protobuf(
            {"keyword": str(keyword)},
            Proto.compiled.SearchAccountByName_pb2.request()
        )
        headers = get_standard_headers(auth_token)
        response = requests.post(endpoint, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        decoded = decode_protobuf(response.content, Proto.compiled.SearchAccountByName_pb2.response)
        return json.loads(json.dumps(decoded, default=str))
    except Exception as e:
        print(f"Search Error: {e}")
        return None

def get_player_stats(authorization, serverurl, mode, uid, match_type="CAREER"):
    try:
        mode = mode.lower()
        url_path = "GetPlayerStats" if mode == "br" else "GetPlayerTCStats"
        url = f"{serverurl.rstrip('/')}/{url_path}"
        
        proto_module = Proto.compiled.PlayerStats_pb2 if mode == "br" else Proto.compiled.PlayerCSStats_pb2
        
        # Map Match Type
        if mode == "br":
            m_mode = {"CAREER": 0, "NORMAL": 1, "RANKED": 2}.get(match_type.upper(), 0)
            payload_data = {"accountid": int(uid), "matchmode": m_mode}
        else:
            m_mode = {"CAREER": 0, "NORMAL": 1, "RANKED": 6}.get(match_type.upper(), 0)
            payload_data = {"accountid": int(uid), "gamemode": 15, "matchmode": m_mode}

        encrypted_payload = encode_protobuf(payload_data, proto_module.request())
        headers = get_standard_headers(authorization)
        
        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        message = decode_protobuf(response.content, proto_module.response)
        return json.loads(json.dumps(message, default=str))
        
    except Exception as e:
        print(f"Stats Error: {e}")
        return None
