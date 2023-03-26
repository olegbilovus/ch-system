from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: str
    sessionid: Optional[str] = None
    username: Optional[str] = None
    userprofileid: Optional[int] = None
    host: Optional[str] = None
    name: Optional[str] = None
    role: Optional[int] = None
    clanid: Optional[int] = None
    serverid: Optional[int] = None
    change_pw: Optional[bool] = None
    creation: Optional[datetime] = None
    lastuse: Optional[datetime] = None

    def __repr__(self):
        return f'[id:{self.id},username:{self.username},userprofileid:{self.userprofileid},' \
               f'name:{self.name},role:{self.role},clanid:{self.clanid},serverid:{self.serverid}]'

    def get_data_select(self, *args):
        return {k: getattr(self, k) for k in args}
