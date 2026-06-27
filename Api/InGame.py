import requests
import Proto.compiled.PlayerPersonalShow_pb2
import Proto.compiled.PlayerStats_pb2
import Proto.compiled.PlayerCSStats_pb2
import Proto.compiled.SearchAccountByName_pb2
from Utilities.until import encode_protobuf, decode_protobuf
import json
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

def get_player_personal_show(serverurl, authorization, account_id, need_gallery_info=False, call_sign_src=7, need_blacklist=False, need_spark_info=False):
    url = f"{serverurl}/GetPlayerPersonalShow"

    payload_data = {
        "accountId": account_id,
        "callSignSrc": call_sign_src,
        "needGalleryInfo": need_gallery_info,
        "needBlacklist": need_blacklist,
        "needSparkInfo": need_spark_info,
    }
    
    encrypted_payload = encode_protobuf(payload_data, Proto.compiled.PlayerPersonalShow_pb2.request())

    # Second Repo jaisa header (Identity use karna zaroori hai compression se bachne ke liye)
    headers = {
      "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
      "Accept": "*/*",
      "Accept-Encoding": "identity", 
      "Authorization": f"Bearer {authorization}",
      "X-GA": "v1 1",
      "ReleaseVersion": RELEASEVERSION,
      "Content-Type": "application/x-protobuf",
      "X-Unity-Version": "2022.3.47f1",
      "Connection": "keep-alive"
    }
    
    try:
        response = requests.post(url, data=encrypted_payload, headers=headers, timeout=10)
        response.raise_for_status()
        raw_res = response.content

        if DEBUG:
            # Debugging ke liye first 10 bytes print karega
            print(f"[GetPlayerPersonalShow] Raw Hex: {raw_res[:10].hex()}")

        # --- SECOND REPO (WORKING) DECODE LOGIC ---
        # Garena IND server hamesha ek 1-byte status bhejta hai (0x00 ya 0x01)
        # Uske baad asli Protobuf start hota hai.
        
        message = Proto.compiled.PlayerPersonalShow_pb2.response()
        
        # Logic 1: Agar data 0x0A (10) se start nahi ho raha, to 1st byte skip karo
        actual_data = raw_res
        if len(raw_res) > 1 and raw_res[0] != 10:
            if raw_res[1] == 10: # Agar 2nd byte 10 hai, to wahan se start karo
                actual_data = raw_res[1:]
            else:
                # Agar fir bhi 10 nahi mila, to Varint length dhoondo (LGR Logic)
                try:
                    (msg_len, start_offset) = decoder._DecodeVarint32(raw_res, 0)
                    actual_data = raw_res[start_offset:start_offset+msg_len]
                except:
                    pass

        try:
            # Sabse pehle Merge use karo (Strict nahi hota)
            message.MergeFromString(actual_data)
            return json.loads(json.dumps(message, default=str))
        except Exception as e:
            # Agar fail ho jaye, to default decode_protobuf try karo
            return decode_protobuf(raw_res, Proto.compiled.PlayerPersonalShow_pb2.response)

    except Exception as e:
        print(f"Error for UID {account_id}: {e}")
        return None

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
