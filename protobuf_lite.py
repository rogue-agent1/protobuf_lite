#!/usr/bin/env python3
"""Simple protobuf-style binary serializer."""
import sys, struct
def encode_varint(n):
    out=b''
    while n>127: out+=bytes([(n&0x7f)|0x80]); n>>=7
    return out+bytes([n])
def decode_varint(data,pos):
    result=shift=0
    while True:
        b=data[pos]; pos+=1; result|=(b&0x7f)<<shift; shift+=7
        if not b&0x80: break
    return result,pos
def encode_field(field_num,wire_type,data):
    tag=encode_varint((field_num<<3)|wire_type)
    if wire_type==0: return tag+encode_varint(data)  # varint
    elif wire_type==2: return tag+encode_varint(len(data))+data  # length-delimited
    return tag
def encode_message(fields):
    out=b''
    for num,wtype,val in fields:
        if isinstance(val,str): val=val.encode()
        out+=encode_field(num,wtype,val)
    return out
# Demo: Person message
msg=encode_message([(1,2,"Rogue"),(2,0,1),(3,2,"rogue@example.com")])
print(f"Encoded: {msg.hex()} ({len(msg)} bytes)")
# Decode
pos=0
while pos<len(msg):
    tag,pos=decode_varint(msg,pos)
    field_num,wire_type=tag>>3,tag&7
    if wire_type==0: val,pos=decode_varint(msg,pos); print(f"  Field {field_num} (varint): {val}")
    elif wire_type==2: ln,pos=decode_varint(msg,pos); print(f"  Field {field_num} (bytes): {msg[pos:pos+ln]}"); pos+=ln
