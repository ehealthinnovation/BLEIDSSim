
class Bolus(object):
    number = 0
    bolus_type = 0
    fast_amount = 0
    extended_amount = 0
    duration = 0
    delay_time = 0
    activation_type = 0

    def __init__(self, number, bolus_type, fast_amount, extended_amount, duration, delay_time, activation_type):
        self.number = number
        self.bolus_type = bolus_type
        self.fast_amount = fast_amount
        self.extended_amount = extended_amount
        self.duration = duration
        self.delay_time = delay_time
        self.activation_type = activation_type
