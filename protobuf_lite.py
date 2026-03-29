#!/usr/bin/env python3
"""Minimal Protocol Buffers encoder/decoder from scratch."""
import sys, struct

VARINT, I64, LEN, I32 = 0, 1, 2, 5

def encode_varint(value):
    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80); value >>= 7
    result.append(value & 0x7F); return bytes(result)

def decode_varint(data, offset):
    result = 0; shift = 0
    while True:
        b = data[offset]; offset += 1
        result |= (b & 0x7F) << shift; shift += 7
        if not (b & 0x80): break
    return result, offset

def encode_field(field_num, wire_type, value):
    tag = encode_varint((field_num << 3) | wire_type)
    if wire_type == VARINT: return tag + encode_varint(value)
    elif wire_type == LEN:
        data = value.encode() if isinstance(value, str) else value
        return tag + encode_varint(len(data)) + data
    elif wire_type == I32: return tag + struct.pack("<i", value)
    elif wire_type == I64: return tag + struct.pack("<q", value)
    return tag

def decode_message(data):
    fields = {}; offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_num = tag >> 3; wire_type = tag & 0x07
        if wire_type == VARINT:
            value, offset = decode_varint(data, offset)
        elif wire_type == LEN:
            length, offset = decode_varint(data, offset)
            value = data[offset:offset+length]; offset += length
        elif wire_type == I32:
            value = struct.unpack_from("<i", data, offset)[0]; offset += 4
        elif wire_type == I64:
            value = struct.unpack_from("<q", data, offset)[0]; offset += 8
        else: break
        fields.setdefault(field_num, []).append((wire_type, value))
    return fields

class MessageBuilder:
    def __init__(self): self.data = bytearray()
    def add_varint(self, field, value): self.data.extend(encode_field(field, VARINT, value)); return self
    def add_string(self, field, value): self.data.extend(encode_field(field, LEN, value)); return self
    def add_bytes(self, field, value): self.data.extend(encode_field(field, LEN, value)); return self
    def add_int32(self, field, value): self.data.extend(encode_field(field, I32, value)); return self
    def add_int64(self, field, value): self.data.extend(encode_field(field, I64, value)); return self
    def add_message(self, field, builder):
        self.data.extend(encode_field(field, LEN, bytes(builder.data))); return self
    def build(self): return bytes(self.data)

def main():
    print("=== Protobuf Lite ===\n")
    msg = MessageBuilder()
    msg.add_varint(1, 42).add_string(2, "Hello Protobuf").add_int32(3, -1).add_varint(4, 1)
    inner = MessageBuilder().add_string(1, "nested").add_varint(2, 99)
    msg.add_message(5, inner)
    encoded = msg.build()
    print(f"Encoded: {len(encoded)} bytes")
    print(f"Hex: {encoded.hex()}")
    fields = decode_message(encoded)
    print(f"\nDecoded fields:")
    for fnum, values in sorted(fields.items()):
        for wtype, val in values:
            if wtype == LEN:
                try: display = val.decode()
                except: display = f"<{len(val)} bytes>"
            else: display = val
            print(f"  Field {fnum} (wire={wtype}): {display}")

if __name__ == "__main__": main()
