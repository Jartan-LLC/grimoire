from dataclasses import dataclass


@dataclass
class Subscription:
    customer_id: int
    active: bool = True
