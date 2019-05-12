import datetime
from typing import Callable

import pytz

from necrobot.match.matchgsheetinfo import MatchGSheetInfo
from necrobot.match.matchinfo import MatchInfo
# from necrobot.match.matchracedata import MatchRaceData
from necrobot.race.raceinfo import RaceInfo
from necrobot.user import userlib
from necrobot.user.necrouser import NecroUser
from necrobot.util import console
from necrobot.util.decorators import commits


class Match(object):
    def __init__(
            self,
            commit_fn,
            racer_1_id,
            racer_2_id,
            match_id=None,
            suggested_time=None,
            r1_confirmed=False,
            r2_confirmed=False,
            r1_unconfirmed=False,
            r2_unconfirmed=False,
            match_info=MatchInfo(),
            cawmentator_id=None,
            channel_id=None,
            gsheet_info=None,
            finish_time=None,
            autogenned=False
    ):
        """Create a `Match` object. There should be no need to call this directly; use `matchutil.make_match` instead, 
        since this needs to interact with the database.
        
        Parameters
        ----------
        commit_fn: Callable
            Function for commiting to the database.
        racer_1_id: int
            The DB user ID of the first racer.
        racer_2_id: int
            The DB user ID of the second racer.
        match_id: int
            The DB unique ID of this match.
        suggested_time: datetime.datetime
            The time the match is suggested for. If no tzinfo, UTC is assumed.
        r1_confirmed: bool
            Whether the first racer has confirmed the match time.
        r2_confirmed: bool
            Whether the second racer has confirmed the match time.
        r1_unconfirmed: bool
            Whether the first racer wishes to unconfirm the match time.
        r2_unconfirmed: bool
            Whether the second racer wishes to unconfirm the match time.
        match_info: MatchInfo
            The type of match.
        cawmentator_id: int
            The DB unique ID of the cawmentator for this match.
        channel_id: int
            The discord.ID of the channel for this match, if any.
        gsheet_info: MatchGSheetInfo
            If this match was created from a GSheet, the worksheet and row it was created from.
        finish_time: datetime.datetime
            The time the match finished at. If no tzinfo, UTC is assumed.
        """
        self._match_id = match_id

        # Racers in the match
        self._racer_1_id = racer_1_id                       # type: int
        self._racer_1 = None                                # type: NecroUser
        self._racer_2_id = racer_2_id                       # type: int
        self._racer_2 = None                                # type: NecroUser

        # Scheduling data
        self._suggested_time = None                         # type: datetime.datetime
        self._finish_time = None                            # type: datetime.datetime
        self._set_suggested_time(suggested_time)
        self._set_finish_time(finish_time)
        self._confirmed_by_r1 = r1_confirmed                # type: bool
        self._confirmed_by_r2 = r2_confirmed                # type: bool
        self._r1_wishes_to_unconfirm = r1_unconfirmed       # type: bool
        self._r2_wishes_to_unconfirm = r2_unconfirmed       # type: bool

        # Format and race data
        self._match_info = match_info                       # type: MatchInfo

        # Other
        self._cawmentator_id = int(cawmentator_id) if cawmentator_id is not None else None  # type: int
        self._channel_id = channel_id                       # type: int
        self._gsheet_info = gsheet_info                     # type: MatchGSheetInfo
        self._autogenned = autogenned                       # type: bool

        # Commit function
        self._commit = commit_fn                            # type: Callable[[], None]

    def __repr__(self):
        return 'Match: <ID={mid}>, <ChannelName={cname}'.format(mid=self.match_id, cname=self.matchroom_name)

    def __eq__(self, other):
        return self.match_id == other.match_id

    def __str__(self):
        return self.matchroom_name

    async def initialize(self):
        self._racer_1 = await userlib.get_user(user_id=self._racer_1_id)
        self._racer_2 = await userlib.get_user(user_id=self._racer_2_id)
        if self._racer_1 is None or self._racer_2 is None:
            raise RuntimeError('Attempted to make a Match object with an unregistered racer.')

    @property
    def format_str(self) -> str:
        """Get a string describing the match format."""
        return self.match_info.format_str

    @property
    def ranked(self):
        return self._match_info.ranked

    @property
    def is_registered(self) -> bool:
        return self._match_id is not None

    @property
    def match_id(self) -> int:
        return self._match_id

    @property
    def racers(self) -> list:
        return [self.racer_1, self.racer_2]

    @property
    def racer_1(self) -> NecroUser:
        return self._racer_1

    @property
    def racer_2(self) -> NecroUser:
        return self._racer_2

    @property
    def suggested_time(self) -> datetime.datetime:
        return self._suggested_time

    @property
    def finish_time(self) -> datetime.datetime:
        return self._finish_time

    @property
    def confirmed_by_r1(self) -> bool:
        return self._confirmed_by_r1

    @property
    def confirmed_by_r2(self) -> bool:
        return self._confirmed_by_r2

    @property
    def r1_wishes_to_unconfirm(self) -> bool:
        return self._r1_wishes_to_unconfirm

    @property
    def r2_wishes_to_unconfirm(self) -> bool:
        return self._r2_wishes_to_unconfirm

    @property
    def has_suggested_time(self) -> bool:
        return self.suggested_time is not None

    @property
    def is_scheduled(self) -> bool:
        return self.has_suggested_time and self.confirmed_by_r1 and self.confirmed_by_r2

    @property
    def is_best_of(self) -> int:
        return self._match_info.is_best_of

    @property
    def number_of_races(self) -> int:
        return self._match_info.max_races

    @property
    def race_info(self) -> RaceInfo:
        return self._match_info.race_info

    @property
    def match_info(self) -> MatchInfo:
        return self._match_info

    @property
    def cawmentator_id(self) -> int:
        return self._cawmentator_id

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def sheet_id(self) -> int:
        return self._gsheet_info.wks_id if self._gsheet_info is not None else None

    @property
    def sheet_row(self) -> int:
        return self._gsheet_info.row if self._gsheet_info is not None else None

    @property
    def autogenned(self) -> bool:
        return self._autogenned

    @property
    def matchroom_name(self) -> str:
        """Get a name for a channel for this match."""
        racer_names = []
        for racer in self.racers:
            racer_matchroom_name = racer.matchroom_name
            if racer_matchroom_name is not None:
                racer_names.append(racer_matchroom_name)

        if len(racer_names) == 2:
            racer_names.sort()
            return '{0}-{1}-{2}'.format(racer_names[0], racer_names[1], self.match_id)
        else:
            return self.race_info.raceroom_name

    @property
    def time_until_match(self) -> datetime.timedelta or None:
        return (self.suggested_time - pytz.utc.localize(datetime.datetime.utcnow())) if self.is_scheduled else None

    async def commit(self) -> None:
        """Write the match to the database."""
        await self._commit(self)

    async def get_cawmentator(self) -> NecroUser or None:
        if self._cawmentator_id is None:
            return None
        return await userlib.get_user(user_id=self._cawmentator_id)

    def racing_in_match(self, user) -> bool:
        """        
        Parameters
        ----------
        user: NecroUser

        Returns
        -------
        bool
            True if the user is in the match.
        """
        return user == self.racer_1 or user == self.racer_2

    # Whether the match has been confirmed by the racer
    def is_confirmed_by(self, racer: NecroUser) -> bool:
        """
        Parameters
        ----------
        racer: NecroUser

        Returns
        -------
        bool
            Whether the Match has been confirmed by racer.
        """
        if racer == self.racer_1:
            return self._confirmed_by_r1
        elif racer == self.racer_2:
            return self._confirmed_by_r2
        else:
            return False

    def set_match_id(self, match_id: int) -> None:
        """Sets the match ID. There should be no need to call this yourself."""
        self._match_id = match_id

    @commits
    def set_finish_time(self, time: datetime.datetime) -> None:
        """Sets the finishing time for the match.
        
        Parameters
        ----------
        time: datetime.datetime
            The time of match finished. If no tzinfo, UTC is assumed.
        """
        self._set_finish_time(time)

    @commits
    def suggest_time(self, time: datetime.datetime) -> None:
        """Unconfirms all previous times and suggests a new time for the match.
        
        Parameters
        ----------
        time: datetime.datetime
            The time to suggest for the match.
        """
        self.force_unconfirm()
        self._set_suggested_time(time)

    @commits
    def confirm_time(self, racer: NecroUser) -> None:
        """Confirms the current suggested time by the given racer. (The match is scheduled after
        both racers have confirmed.)
        
        Parameters
        ----------
        racer: NecroUser
        """
        if racer == self.racer_1:
            self._confirmed_by_r1 = True
        elif racer == self.racer_2:
            self._confirmed_by_r2 = True

    @commits
    def unconfirm_time(self, racer: NecroUser) -> None:
        """Attempts to unconfirm the current suggested time by the given racer. This deletes the 
        suggested time if either the match is not already scheduled or the other racer has also 
        indicated a desire to unconfirm.
        
        Parameters
        ----------
        racer: NecroUser
        """
        if racer == self.racer_1:
            if (not self._confirmed_by_r2) or self._r2_wishes_to_unconfirm:
                self.force_unconfirm()
            else:
                self._r1_wishes_to_unconfirm = True
        elif racer == self.racer_2:
            if (not self._confirmed_by_r1) or self._r1_wishes_to_unconfirm:
                self.force_unconfirm()
            else:
                self._r2_wishes_to_unconfirm = True

    @commits
    def force_confirm(self) -> None:
        """Forces all racers to confirm the suggested time."""
        if self._suggested_time is None:
            console.warning('Tried to force_confirm a Match with no suggested time.')
            return
        self._confirmed_by_r1 = True
        self._confirmed_by_r2 = True
        self._r1_wishes_to_unconfirm = False
        self._r2_wishes_to_unconfirm = False

    @commits
    def force_unconfirm(self) -> None:
        """Unconfirms and deletes any current suggested time."""
        self._confirmed_by_r1 = False
        self._confirmed_by_r2 = False
        self._r1_wishes_to_unconfirm = False
        self._r2_wishes_to_unconfirm = False
        self._suggested_time = None

    @commits
    def set_repeat(self, number: int) -> None:
        """Sets the match type to be a repeat-X.
        
        Parameters
        ----------
        number: int
            The number of races to be played in the match.
        """
        self._match_info.is_best_of = False
        self._match_info.max_races = number

    @commits
    def set_best_of(self, number: int) -> None:
        """Sets the match type to be a best-of-X.
        
        Parameters
        ----------
        number: int
            The maximum number of races to be played (the match will be a best-of-number).
        """
        self._match_info.is_best_of = True
        self._match_info.max_races = number

    @commits
    def set_race_info(self, race_info: RaceInfo) -> None:
        """Sets the type of races to be done in the match.
        
        Parameters
        ----------
        race_info: RaceInfo
            The new match RaceInfo.
        """
        self._match_info.race_info = race_info

    @commits
    def set_cawmentator_id(self, cawmentator_id: int or None) -> None:
        """Sets a cawmentator for the match. Using cawmentator_id = None will remove cawmentary.
        
        Parameters
        ----------
        cawmentator_id: Optional[int]
            The user ID of the cawmentator.
        """
        self._cawmentator_id = cawmentator_id

    @commits
    def set_channel_id(self, channel_id: int or None) -> None:
        """Sets a channel ID for the match.
        
        Parameters
        ----------
        channel_id: Optional[int]
            A discord.Channel ID
        """
        self._channel_id = int(channel_id)

    @commits
    def raw_update(self, **kwargs):
        if 'suggested_time' in kwargs:
            self._set_suggested_time(kwargs['suggested_time'])
        if 'r1_confirmed' in kwargs:
            self._confirmed_by_r1 = kwargs['r1_confirmed']
        if 'r2_confirmed' in kwargs:
            self._confirmed_by_r2 = kwargs['r2_confirmed']
        if 'r1_unconfirmed' in kwargs:
            self._r1_wishes_to_unconfirm = kwargs['r1_unconfirmed']
        if 'r2_unconfirmed' in kwargs:
            self._r2_wishes_to_unconfirm = kwargs['r2_unconfirmed']
        if 'match_info' in kwargs:
            self._match_info = kwargs['match_info']
        if 'cawmentator_id' in kwargs:
            self._cawmentator_id = kwargs['cawmentator_id']
        if 'channel_id' in kwargs:
            self._channel_id = kwargs['channel_id']
        if 'gsheet_info' in kwargs:
            self._gsheet_info = kwargs['gsheet_info']
        if 'finish_time' in kwargs:
            self._finish_time = kwargs['finish_time']

    def _set_suggested_time(self, time: datetime.datetime or None) -> None:
        if time is None:
            self._suggested_time = None
            return
        if time.tzinfo is None:
            time = pytz.utc.localize(time)
        self._suggested_time = time.astimezone(pytz.utc)

    def _set_finish_time(self, time: datetime.datetime or None) -> None:
        if time is None:
            self._finish_time = None
            return
        if time.tzinfo is None:
            time = pytz.utc.localize(time)
        self._finish_time = time.astimezone(pytz.utc)
