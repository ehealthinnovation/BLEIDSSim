import struct

def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])[2::]

def bytes(num):
    return hex(num >> 8), hex(num & 0xFF)
