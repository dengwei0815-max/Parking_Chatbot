class Reservation:
    """
    Data model for a parking reservation.
    """
    def __init__(self, name, car_number, period):
        self.name = name
        self.car_number = car_number
        self.period = period
        self.status = "pending"  # pending, confirmed, refused