import requests
import json
import Proto.compiled.PlayerPersonalShow_pb2
import Proto.compiled.PlayerStats_pb2
import Proto.compiled.PlayerCSStats_pb2
import Proto.compiled.SearchAccountByName_pb2
from Utilities.until import encode_protobuf, decode_protobuf
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG

# --- Helper: Missing Field Sniffer (Yeh tujhe batayega server kya bhej raha hai) ---
def inspect_binary_fields(raw_data):
    print(f"\n[!!!] --- INSPECTING DATA ---")
    print(f"[!] Total Bytes: {len(raw_data)}")
    pos = 0
    tags = []
    while pos < len(raw_data):
        try:
            byte = raw_data[pos]
            tag = byte >> 3
            if tag > 0 and tag < 200:
                tags.append(tag)
            pos += 1
        except:
            break
    print(f"[!] Fields Found (Tags): {sorted(list(set(tags)))}")
    print(f"[!!!] --- END INSPECTION ---\n")

def search_account_by_keyword(server_url, auth_token, keyword):
    try:
        endpoint = f"{server_url}/FuzzySearchAccountByName"
        payload = encode_protobuf({"keyword": str(keyword)}, Proto.compiled.SearchAccountByName_pb2.request())
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            "Authorization": f"Bearer {auth_token}",
            "ReleaseVersion": RELEASEVERSION,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(endpoint, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        decoded = decode_protobuf(response.content, Proto.compiled.SearchAccountByName_pb2.response)
        return json.loads(json.dumps(decoded, default=str))
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_player_personal_show(serverurl, authorization, account_id, need_gallery_info=False, call_sign_src=7, need_blacklist=False, need_spark_info=False):
    payload_data = {
        "accountId": account_id,
        "callSignSrc": call_sign_src,
        "needGalleryInfo": need_gallery_info,
        "needBlacklist": need_blacklist,
        "needSparkInfo": need_spark_info,
    }
    encrypted_payload = encode_protobuf(payload_data, Proto.compiled.PlayerPersonalShow_pb2.request())

    headers = {
        "Host": "client.ind.freefiremobile.com",
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Authorization": f"Bearer {authorization}",
        "ReleaseVersion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url = f"{serverurl}/GetPlayerPersonalShow"
    
    try:
        response = requests.post(url, data=encrypted_payload, headers=headers)
        response.raise_for_status()
        
        # 1. Normal Decode Try
        message = decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)
        return json.loads(json.dumps(message, default=str))
        
    except Exception as e:
        # 2. Agar fail hua toh ye sniffer chalao
        print(f"[!] CRITICAL PARSING ERROR: {e}")
        inspect_binary_fields(response.content) 
        return {
            "status": "error", 
            "message": "Schema update required", 
            "check_logs": "Look for [!!!] INSPECTING DATA in logs"
        }

def get_player_stats(authorization, serverurl, mode, uid, match_type="CAREER"):
    try:
        uid = int(uid)
        mode = mode.lower()
        match_type = match_type.upper()
        
        if mode == "br":
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 2}
            url = f"{serverurl}/GetPlayerStats"
            proto_module = Proto.compiled.PlayerStats_pb2
        else:
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 6}
            url = f"{serverurl}/GetPlayerTCStats"
            proto_module = Proto.compiled.PlayerCSStats_pb2
        
        matchmode = type_mapping.get(match_type, 0)
        payload_data = {"accountid": uid, "matchmode": matchmode}
        if mode == "cs": payload_data["gamemode"] = 15
            
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
        return json.loads(json.dumps(message, default=str))
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
