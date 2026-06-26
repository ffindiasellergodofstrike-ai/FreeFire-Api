"""
Protobuf Binary Parser - Extract field information from raw protobuf bytes

Usage:
    from Proto.BinaryAnalyzer import analyze_protobuf_structure
    
    # Parse raw protobuf bytes and show field structure
    analyze_protobuf_structure(response_bytes, max_fields=50)
"""

def parse_varint(data, offset):
    """Parse a varint from protobuf data"""
    result = 0
    shift = 0
    while True:
        byte = data[offset]
        result |= (byte & 0x7f) << shift
        offset += 1
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result, offset


def analyze_protobuf_structure(data, max_fields=50):
    """
    Analyze a raw protobuf response and show field numbers and types
    
    Args:
        data (bytes): Raw protobuf data
        max_fields (int): Maximum fields to show
    
    Returns:
        dict: Field information {field_number: (wire_type, count)}
    """
    offset = 0
    fields = {}
    field_count = 0
    
    print(f"Analyzing {len(data)} bytes of protobuf data...\n")
    print(f"{'Field':<8} {'Wire Type':<12} {'Description':<30} {'Count':<6}")
    print("-" * 60)
    
    while offset < len(data) and field_count < max_fields:
        try:
            # Parse field header (varint)
            key, offset = parse_varint(data, offset)
            field_number = key >> 3
            wire_type = key & 0x07
            
            # Wire types: 0=varint, 1=64-bit, 2=length-delimited, 3=start group, 4=end group, 5=32-bit
            wire_type_names = {
                0: "varint",
                1: "64-bit",
                2: "length-delimited",
                3: "start group",
                4: "end group",
                5: "32-bit"
            }
            
            if field_number not in fields:
                fields[field_number] = (wire_type, 0)
                field_count += 1
            
            wire_name = wire_type_names.get(wire_type, "unknown")
            fields[field_number] = (wire_type, fields[field_number][1] + 1)
            
            # Skip field value based on wire type
            if wire_type == 0:  # varint
                _, offset = parse_varint(data, offset)
            elif wire_type == 1:  # 64-bit
                offset += 8
            elif wire_type == 2:  # length-delimited
                length, offset = parse_varint(data, offset)
                offset += length
            elif wire_type == 5:  # 32-bit
                offset += 4
            else:
                break
            
            count = fields[field_number][1]
            print(f"{field_number:<8} {wire_name:<12} {'(appears ' + str(count) + ' time(s)'):<30} {count:<6}")
        
        except (IndexError, ValueError) as e:
            print(f"\nParsing stopped at offset {offset}: {e}")
            break
    
    print("\n" + "=" * 60)
    print(f"Found {len(fields)} unique fields")
    print("\nField summary:")
    for field_num in sorted(fields.keys()):
        wire_type, count = fields[field_num]
        wire_names = {0: "varint", 1: "64-bit", 2: "length-delimited", 5: "32-bit"}
        print(f"  Field {field_num}: {wire_names.get(wire_type, 'unknown')} (count: {count})")
    
    return fields


if __name__ == "__main__":
    # Test with sample data
    import sys
    if len(sys.argv) > 1:
        try:
            # If hex string provided
            data = bytes.fromhex(sys.argv[1])
            analyze_protobuf_structure(data)
        except ValueError:
            print("Invalid hex string")
