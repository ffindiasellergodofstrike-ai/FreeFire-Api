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

app = Flask(__name__)

def get_standard_headers(auth_token):
    """Unified headers to prevent mismatches"""
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

def get_player_personal_show(serverurl, authorization, account_id):
    """
    Fixed version: Removed hardcoded Host and Content-Length
    """
    url = f"{serverurl.rstrip('/')}/GetPlayerPersonalShow"

    try:
        payload_data = {
            "accountId": int(account_id),
            "callSignSrc": 7,
            "needGalleryInfo": False,
            "needBlacklist": False,
            "needSparkInfo": False,
        }
        
        encrypted_payload = encode_protobuf(payload_data, Proto.compiled.PlayerPersonalShow_pb2.request())
        headers = get_standard_headers(authorization)
        
        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=15)
        
        if DEBUG:
            print(f"[DEBUG] URL: {url}")
            print(f"[DEBUG] Response Status: {response.status_code}")
        
        response.raise_for_status()
        
        # Decode protobuf response
        message = decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)
        return json.loads(json.dumps(message, default=str))
        
    except Exception as e:
        print(f"Parsing Error in PersonalShow: {e}")
        # This shows exactly which field failed in OB54
        traceback.print_exc() 
        return None

def get_player_stats(authorization, serverurl, mode, uid, match_type="CAREER"):
    try:
        mode = mode.lower()
        url_path = "GetPlayerStats" if mode == "br" else "GetPlayerTCStats"
        url = f"{serverurl.rstrip('/')}/{url_path}"
        
        proto_module = Proto.compiled.PlayerStats_pb2 if mode == "br" else Proto.compiled.PlayerCSStats_pb2
        
        # Match Mode Mapping
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

# --- FLASK ROUTES (Fixes your local 404) ---

@app.route('/get_player_personal_show', methods=['GET'])
def api_personal_show():
    # Example: /get_player_personal_show?server=ind&uid=87479880
    uid = request.args.get('uid')
    region = request.args.get('server', 'ind')
    
    # You need to provide a valid token here
    # token = "YOUR_OAUTH_ACCESS_TOKEN"
    # server_url = f"https://client.{region}.freefiremobile.com"
    
    # For now, this is a placeholder for your logic:
    # result = get_player_personal_show(server_url, token, uid)
    
    return jsonify({"status": "route_found", "message": "Call this function with your logic"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
