from dataclasses import dataclass, asdict

@dataclass
class PropertyResult:
    parcel_id: str
    owner: str
    address: str

    def to_dict(self):
        return asdict(self)
