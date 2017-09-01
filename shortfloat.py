#!/usr/bin/env python

import math

from decimal import Decimal

reservedValue = 0x07FE
mderSFloatMax = 20450000000.0
mderFloatMax = 8.388604999999999e+133
mderSFLoatEpsilon = 1e-8
mderSFloatMantissaMax = 0x07FD
mderSFloatExponentMax = 7
mderSFloatExponentMin = -8
mderSFloatPrecision = 10000
mderPositiveInfinity = 0x07FE
mderNaN = 0x07FF
mderNRes = 0x0800
mderReservedValue = 0x0801
mderNegativeInfinity = 0x0802


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

	floatMantissa = float(mantissa)

	return floatMantissa * float(pow(10, float(exponent)/1))


def float_to_shortfloat(number):
	result = float(mderNaN)
	
	if float(number) > float(mderSFloatMax):
		return float(mderPositiveInfinity)
	elif float(number) < float(-mderFloatMax):
		return float(mderNegativeInfinity)
	elif (float(number) >= float(-mderSFLoatEpsilon) and float(number) <= float(mderSFLoatEpsilon)):
		return 0

	if Decimal(number) > 0:
		sgn = +1
	else:
		sgn = -1

	mantissa = math.fabs(Decimal(number))
	exponent = int(0)

	#scale up if number is too big
	while (mantissa > Decimal(mderSFloatMantissaMax)):
		mantissa /= 10.0
        exponent+=1
        if (Decimal(exponent) > Decimal(mderSFloatExponentMax)):
        	if (sgn > 0):
        		result = 0
        	else:
        		result = 1

        	return float(result)

	# scale down if number is too small
	while (mantissa < 1):
		mantissa *= 10
        exponent-=1
    	if (int(exponent) < mderSFloatExponentMin):
        	result = 0
        	return float(result)

	# scale down if number needs more precision
	smantissa = round(mantissa * float(mderSFloatPrecision))
	rmantissa = round(mantissa) * float(mderSFloatPrecision)
	mdiff = abs(smantissa - rmantissa)
	while (mdiff > 0.5 and exponent > int(mderSFloatExponentMin) and (mantissa * 10) <= Decimal(mderSFloatMantissaMax)):
		exponent -=1
		mantissa *= 10
        smantissa = round(mantissa * float(mderSFloatPrecision))
        rmantissa = round(mantissa) * float(mderSFloatPrecision)
        mdiff = abs(smantissa - rmantissa)

	int_mantissa = int(round(sgn * mantissa))
	adjustedExponent = int(exponent) & 0xF
	shiftedExponent = int(adjustedExponent) << 12
	adjustedMantissa = int(int_mantissa & 0xFFF)
	output = int(adjustedMantissa) | shiftedExponent
	
	return int(output)
