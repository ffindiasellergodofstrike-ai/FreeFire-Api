import requests
import Proto.compiled.PlayerPersonalShow_pb2
import Proto.compiled.PlayerStats_pb2
import Proto.compiled.PlayerCSStats_pb2
import Proto.compiled.SearchAccountByName_pb2
from Utilities.until import encode_protobuf, decode_protobuf
import json
import traceback
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG

def search_account_by_keyword(server_url, auth_token, keyword):
    try:
        # Fix: Ensure no double slashes in URL
        endpoint = f"{server_url.rstrip('/')}/FuzzySearchAccountByName"
        try:
            payload = encode_protobuf(
                {"keyword": str(keyword)},
                Proto.compiled.SearchAccountByName_pb2.request()
            )
        except Exception as e:
            raise ValueError(f"Failed to encode protobuf payload: {e}")

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
        
        decoded = decode_protobuf(response.content, Proto.compiled.SearchAccountByName_pb2.response)
        return json.loads(json.dumps(decoded, default=str))
    except Exception as e:
        print(f"Search Error: {e}")
        return None

def get_player_personal_show(serverurl, authorization, account_id, need_gallery_info=False, call_sign_src=7, need_blacklist=False, need_spark_info=False):
    url = f"{serverurl.rstrip('/')}/GetPlayerPersonalShow"

    try:
        # Request data
        payload_dict = {
            "accountId": int(account_id),
            "callSignSrc": int(call_sign_src),
            "needGalleryInfo": bool(need_gallery_info),
            "needBlacklist": bool(need_blacklist),
            "needSparkInfo": bool(need_spark_info),
        }
        
        encrypted_payload = encode_protobuf(payload_dict, Proto.compiled.PlayerPersonalShow_pb2.request())
        
        headers = {
            "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Authorization": f"Bearer {authorization}",
            "X-GA": "v1 1",
            "ReleaseVersion": RELEASEVERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2022.3.47f1",
            "Content-Length": str(len(encrypted_payload))
        }

        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=15)
        response.raise_for_status()

        # Decoding (Aapka function dictionary return karta hai)
        data = decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)
        
        # Agar data string hai to JSON mein convert karein
        if isinstance(data, str):
            data = json.loads(data)

        # --- OB54 NEW FIELDS FIX (Safe Dictionary Access) ---
        # Hum check kar rahe hain ki kya data mein basicinfo aur achievement_points hain
        
        basic_info = data.get('basicinfo', {})
        
        # Naya section banate hain result mein dikhane ke liye
        data['ob54_debug'] = {
            "achievement_points": basic_info.get('achievement_points', "Not Found"),
            "achievement_rank": basic_info.get('achievement_rank_id', "Not Found"),
            # Agar proto updated hai to ye fields milengi
            "has_achievement_info": "achievement_info" in data 
        }

        return data

    except Exception as e:
        # Error aane par hum pura error message return karenge taaki debug ho sake
        return {
            "status": "failed", 
            "error": str(e),
            "type": str(type(e).__name__)
        }
def get_player_stats(authorization, serverurl, mode, uid, match_type="CAREER"):
    try:
        uid = int(uid)
        mode = mode.lower()
        match_type = match_type.upper()
        
        base_url = serverurl.rstrip('/')
        
        if mode == "br":
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 2}
            url = f"{base_url}/GetPlayerStats"
            proto_module = Proto.compiled.PlayerStats_pb2
        else:
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 6}
            url = f"{base_url}/GetPlayerTCStats"
            proto_module = Proto.compiled.PlayerCSStats_pb2
        
        matchmode = type_mapping.get(match_type, 0)
        
        if mode == "br":
            payload_data = {"accountid": uid, "matchmode": matchmode}
        else:
            payload_data = {"accountid": uid, "gamemode": 15, "matchmode": matchmode}
        
        encrypted_payload = encode_protobuf(payload_data, proto_module.request())
        
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {authorization}",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/x-www-form-urlencoded",
            'Content-Length': str(len(encrypted_payload))
        }
        
        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=15)
        response.raise_for_status()
        
        message = decode_protobuf(response.content, proto_module.response)
        return json.loads(json.dumps(message, default=str))
        
    except Exception as e:
        print(f"Stats Error: {e}")
        return None
