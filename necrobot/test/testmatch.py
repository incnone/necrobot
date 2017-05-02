import datetime
from necrobot.match.match import Match
from necrobot.match.matchinfo import MatchInfo
from necrobot.match import matchutil
from necrobot.user import userlib


async def get_match(
        r1_name: str,
        r2_name: str,
        time: datetime.datetime or None,
        cawmentator_name: str or None
) -> Match:
    racer_1 = await userlib.get_user(any_name=r1_name, register=False)
    racer_2 = await userlib.get_user(any_name=r2_name, register=False)
    cawmentator = await userlib.get_user(rtmp_name=cawmentator_name)
    cawmentator_id = cawmentator.user_id if cawmentator is not None else None

    match_info = MatchInfo(ranked=True)
    return await matchutil.make_match(
        racer_1_id=racer_1.user_id,
        racer_2_id=racer_2.user_id,
        match_info=match_info,
        suggested_time=time,
        r1_confirmed=time is not None,
        r2_confirmed=time is not None,
        cawmentator_id=cawmentator_id,
        register=False
    )
