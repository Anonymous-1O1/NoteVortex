from dataclasses import dataclass,field
from datetime import datetime

@dataclass
class User:
    _id:str
    email:str
    password:str
    notes:list[str] = field(default_factory=list)

@dataclass
class Note:
    _id:str
    title:str
    content:str
    created:str=datetime.today().strftime("%d/%m/%Y")
    last_edited:str=datetime.today().strftime("%d/%m/%Y")
    pinned:bool=False