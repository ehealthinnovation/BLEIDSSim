#!/usr/bin/env python

import math

from decimal import Decimal

RESERVED_VALUE = 0x07FE
MDER_SFLOAT_MAX = 20450000000.0
MDER_FLOAT_MAX = 8.388604999999999e+133
MDER_SFLOAT_EPSILON = 1e-8
MDER_SFLOAT_MANTISSA_MAX = 0x07FD
MDER_SFLOAT_EXPONENT_MAX = 7
MDER_SFLOAT_EXPONENT_MIN = -8
MDER_SFLOAT_PRECISION = 10000
MDER_POSITIVE_INFINITY = 0x07FE
MDER_NAN = 0x07FF
MDER_NRES = 0x0800
MDER_RESERVED_VALUE = 0x0801
MDER_NEGATIVE_INFINITY = 0x0802


def shortfloat_to_float(short_float_number):
	number = int(short_float_number, 16)
	
	#remove the mantissa portion of the number using bit shifting
	exponent = number >> 12
	
	if exponent >= 8:
		# exponent is signed and should be negative 8 = -8, 9 = -7, ... 15 = -1. Range is 7 to -8
		exponent = -((0x000F + 1) - exponent)

	# remove exponent portion of the number using bit mask
	mantissa = number & 4095

	if mantissa >= 2048:
		# mantissa is signed and should be negative 2048 = -2048, 2049 = -2047, ... 4095 = -1. Range is 2047 to -2048
		mantissa = -((0x0FFF + 1) - mantissa)

	float_mantissa = float(mantissa)

	return float_mantissa * float(pow(10, float(exponent)/1))


def float_to_shortfloat(number):
	result = float(MDER_NAN)
	
	if float(number) > float(MDER_SFLOAT_MAX):
		return float(MDER_POSITIVE_INFINITY)
	elif float(number) < float(-MDER_FLOAT_MAX):
		return float(MDER_NEGATIVE_INFINITY)
	elif (float(number) >= float(-MDER_SFLOAT_EPSILON) and float(number) <= float(MDER_SFLOAT_EPSILON)):
		return 0

	if Decimal(number) > 0:
		sgn = +1
	else:
		sgn = -1

	mantissa = math.fabs(Decimal(number))
	exponent = int(0)

	#scale up if number is too big
	while (mantissa > Decimal(MDER_SFLOAT_MANTISSA_MAX)):
		mantissa /= 10.0
		exponent+=1
		if (Decimal(exponent) > Decimal(MDER_SFLOAT_EXPONENT_MAX)):
			if (sgn > 0):
				result = 0
			else:
				result = 1

			return float(result)

	# scale down if number is too small
	while (mantissa < 1):
		mantissa *= 10
		exponent-=1
		if (int(exponent) < MDER_SFLOAT_EXPONENT_MIN):
			result = 0
			return float(result)

	# scale down if number needs more precision
	smantissa = round(mantissa * float(MDER_SFLOAT_PRECISION))
	rmantissa = round(mantissa) * float(MDER_SFLOAT_PRECISION)
	mdiff = abs(smantissa - rmantissa)
	while (mdiff > 0.5 and exponent > int(MDER_SFLOAT_EXPONENT_MIN) and (mantissa * 10) <= Decimal(MDER_SFLOAT_MANTISSA_MAX)):
		exponent -=1
		mantissa *= 10
		smantissa = round(mantissa * float(MDER_SFLOAT_PRECISION))
		rmantissa = round(mantissa) * float(MDER_SFLOAT_PRECISION)
		mdiff = abs(smantissa - rmantissa)

	int_mantissa = int(round(sgn * mantissa))
	adjusted_exponent = int(exponent) & 0xF
	shifted_exponent = int(adjusted_exponent) << 12
	adjusted_mantissa = int(int_mantissa & 0xFFF)
	output = int(adjusted_mantissa) | shifted_exponent
	
	return int(output)
