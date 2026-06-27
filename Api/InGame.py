import requests
import Proto.compiled.PlayerPersonalShow_pb2
import Proto.compiled.PlayerStats_pb2
import Proto.compiled.PlayerCSStats_pb2
import Proto.compiled.SearchAccountByName_pb2
from Utilities.until import encode_protobuf, decode_protobuf
import json
import zlib
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG
import google.protobuf.internal.decoder as decoder # Ye zaroori hai

def search_account_by_keyword(server_url, auth_token, keyword):
    """
    Perform a fuzzy account search by keyword.
    """
    try:
        # --- Endpoint & Payload ---
        endpoint = f"{server_url}/FuzzySearchAccountByName"
        try:
            payload = encode_protobuf(
                {"keyword": str(keyword)},
                Proto.compiled.SearchAccountByName_pb2.request()
            )
        except Exception as e:
            raise ValueError(f"Failed to encode protobuf payload: {e}")

        # --- Request Headers ---
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

        # --- Execute Request ---
        try:
            response = requests.post(endpoint, data=payload, headers=headers, timeout=15)
            response.raise_for_status()
            if DEBUG:
                print("[I] RES:", response.content, "\n")
        except requests.exceptions.Timeout:
            raise ConnectionError("Request timed out while contacting server.")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Failed to connect to the server.")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"HTTP error {response.status_code}: {e}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request error: {e}")

        if not response.content:
            raise RuntimeError("Empty response received from server.")

        # --- Decode Response ---
        try:
            decoded = decode_protobuf(
                response.content,
                Proto.compiled.SearchAccountByName_pb2.response
            )
        except Exception as e:
            raise ValueError(f"Failed to decode protobuf response: {e}")

        return json.loads(json.dumps(decoded, default=str))

    except Exception as e:
        raise RuntimeError(f"Unhandled error in search_account_by_keyword: {e}")

def get_player_personal_show(serverurl, authorization, account_id, **kwargs):
    url = f"{serverurl}/GetPlayerPersonalShow"
    
    req = Proto.compiled.PlayerPersonalShow_pb2.request()
    req.accountId = int(account_id)
    req.callSignSrc = 7
    
    # Payload
    payload = encode_protobuf({"accountId": int(account_id), "callSignSrc": 7}, Proto.compiled.PlayerPersonalShow_pb2.request())

    headers = {
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Authorization": f"Bearer {authorization}",
        "Content-Type": "application/x-protobuf", # Octet-stream ki jagah ye use karein
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASEVERSION
    }
    
    response = requests.post(url, data=payload, headers=headers, timeout=10)
    
    # Dictionary return karo
    return decode_protobuf(response.content, Proto.compiled.PlayerPersonalShow_pb2.response)


def get_player_stats(authorization, serverurl, mode, uid, match_type="CAREER"):
    """
    Get player statistics for BR or CS mode
    """
    try:
        # Validate inputs
        if not isinstance(uid, (int, str)) or not str(uid).isdigit():
            raise ValueError(f"Invalid UID: {uid}. Must be a numeric value.")
        
        uid = int(uid)
        
        mode = mode.lower()
        if mode not in ["br", "cs"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'br' or 'cs'")
        
        match_type = match_type.upper()
        if match_type not in ["CAREER", "NORMAL", "RANKED"]:
            raise ValueError(f"Invalid match type: {match_type}. Must be 'CAREER', 'NORMAL', or 'RANKED'")
        
        if mode == "br":
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 2}
            url = f"{serverurl}/GetPlayerStats"
            proto_module = Proto.compiled.PlayerStats_pb2
        else:
            type_mapping = {"CAREER": 0, "NORMAL": 1, "RANKED": 6}
            url = f"{serverurl}/GetPlayerTCStats"
            proto_module = Proto.compiled.PlayerCSStats_pb2
        
        matchmode = type_mapping[match_type]
        
        if mode == "br":
            payload_data = {"accountid": uid, "matchmode": matchmode}
        else:
            payload_data = {"accountid": uid, "gamemode": 15, "matchmode": matchmode}
        
        try:
            encrypted_payload = encode_protobuf(payload_data, proto_module.request())
        except Exception as e:
            raise Exception(f"Failed to encode protobuf payload: {str(e)}")
        
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
            'Expect': "100-continue",
            'Authorization': f"Bearer {authorization}",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(url, data=encrypted_payload, headers=headers, timeout=30)
            response.raise_for_status()
            if DEBUG:
                print("[I] RES:", response.content, "\n")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
        
        if not response.content:
            raise Exception("Empty response from server")
        
        try:
            message = decode_protobuf(response.content, proto_module.response)
        except Exception as e:
            raise Exception(f"Failed to decode protobuf response: {str(e)}")
        
        return message
        
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")
