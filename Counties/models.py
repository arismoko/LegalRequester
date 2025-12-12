from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ParcelInformation:
    parcel_id: Optional[str]
    owner: Optional[str]
    address: str
    county_url: str = ""

    def to_dict(self):
        return asdict(self)
