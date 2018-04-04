import struct

def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])[2::]

def bytes(num):
    return hex(num >> 8), hex(num & 0xFF)

def is_set(value, bit):
    return value & 2**bit != 0

def bytes_to_int16(value):
	str = ''.join(map(lambda b: format(b, "02x"), value))
	return int(str, 16)

def get_class_attributes(class_name):
	this_class = class_name
	attributes = [attr for attr in dir(this_class) if not callable(getattr(this_class, attr)) and not attr.startswith("__")]
	return attributes

def bit(value, bit):
	return value & 2**bit != 0

def find_complement(num):
        bits = '{0:b}'.format(num)
        complement_bits = ''.join('1' if bit == '0' else '0' for bit in bits)
        return int(complement_bits, 2)
