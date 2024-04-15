#!/usr/bin/env python3
# coding=utf-8

"""
This module contains several functions with relation to time
"""

#@sk import
from __future__ import annotations

import os
import datetime
from abc import ABC, abstractmethod


import pandas
from pandas import Timestamp, Timedelta
from typing import Sequence, Any
from enum import Enum, auto

from ._o_globalstate import logger, strict
from ._o_error import ShouldNeverSeeError
from ._o_basefunc import isinstanceAll


class _time(ABC):
    def __init__(self, year: int = 0, month: int = 0, day: int = 0, hour: int = 0, minute: int = 0, second: int = 0, msecond: int = 0):
        self._values = [year, month, day, hour, minute, second, msecond]

    @property
    def year(self):
        return self._values[0]
    @year.setter
    def year(self, val: int):
        assert isinstance(val, int)
        self._values[0] = val

    @property
    def month(self):
        return self._values[1]
    @month.setter
    def month(self, val: int):
        assert isinstance(val, int)
        self._values[1] = val

    @property
    def day(self):
        return self._values[2]
    @day.setter
    def day(self, val: int):
        assert isinstance(val, int)
        self._values[2] = val

    @property
    def hour(self):
        return self._values[3]
    @hour.setter
    def hour(self, val: int):
        assert isinstance(val, int)
        self._values[3] = val

    @property
    def minute(self):
        return self._values[4]
    @minute.setter
    def minute(self, val: int):
        assert isinstance(val, int)
        self._values[4] = val

    @property
    def second(self):
        return self._values[5]
    @second.setter
    def second(self, val: int):
        assert isinstance(val, int)
        self._values[5] = val

    @property
    def msecond(self):
        return self._values[6]
    @msecond.setter
    def msecond(self, val: int):
        assert isinstance(val, int)
        self._values[6] = val

class realevel(Enum):
    UNKNOWN = -1
    YEAR = 0
    MONTH = 1
    DAY = 2
    HOUR = 3
    MINUTE = 4
    SECOND = 5
    MSECOND = 6
    ALL = -2

    @classmethod
    def getTimescale(cls, s: str):
        assert isinstance(s, str)
        if len(s) == 4:
            return cls.YEAR
        elif len(s) == 6:
            return cls.MONTH
        elif len(s) == 8:
            return cls.DAY
        elif len(s) == 10:
            return cls.HOUR
        elif len(s) == 12:
            return cls.MINUTE
        elif len(s) == 14:
            return cls.SECOND
        else:
            logger.error(f"Wrong length for ymdhms string: {len(s)}")
            raise RuntimeError

    def __gt__(self, rv2: realevel):
        if not isinstance(rv2, realevel):
            raise TypeError
        return self.value > rv2.value
    
    def __lt__(self, rv2: realevel):
        if not isinstance(rv2, realevel):
            raise TypeError
        return self.value < rv2.value

    def __ge__(self, rv2: realevel):
        if not isinstance(rv2, realevel):
            raise TypeError
        return self.value >= rv2.value
    
    def __le__(self, rv2: realevel):
        if not isinstance(rv2, realevel):
            raise TypeError
        return self.value <= rv2.value



class freetime(_time):
    def __init__(self, *args, **kwargs):
        _time.__init__(self, *args, **kwargs)

    def __copy__(self):
        return freetime(self.year, self.month, self.day, self.hour, self.minute, self.second, self.msecond)

    def __str__(self):
        """
        Doesn't consider <msecond> now @2024-04-08 22:38:26
        """
        return str(self.year) + "/" + str(self.month) + "/" + str(self.day) + " " + str(self.hour) + ":" + str(self.minute) + ":" + str(self.second)
    
    def __repr__(self):
        return self.__str__()


    def __iadd__(self, ft2: freetime):
        assert isinstance(ft2, freetime)
        self._values = [self._values[i] + ft2._values[i] for i in range(len(self._values))]
        return self
    
    def __add__(self, ft2: _time):
        if isinstance(ft2, freetime):
            ftN = self.copy()
            ftN += ft2
            return ftN
        elif isinstance(ft2, realtime):
            return ft2 + self
        else:
            raise TypeError

    def __isub__(self, ft2: freetime):
        assert isinstance(ft2, freetime)
        self._values = [self._values[i] - ft2._values[i] for i in range(len(self._values))]
        return self
    
    def __sub__(self, ft2: freetime):
        assert isinstance(ft2, freetime)
        ftN = self.copy()
        ftN -= ft2
        return ftN

    def add(self, ft2: freetime):
        self += ft2
        return self
    
    def sub(self, ft2: freetime):
        self -= ft2
        return self

    def copy(self):
        return self.__copy__()

    def sim(self):
        seconds: int = self.day * 86400 + self.hour * 3600 + self.minute * 60 + self.second
        if seconds >= 0:
            self.day = seconds // 86400
        else:
            self.day = int((seconds - 86399) / 86400)
        seconds -= self.day * 86400
        assert seconds >= 0
        self.hour = seconds // 3600
        seconds -= self.hour * 3600
        self.minute = seconds // 60
        self.second = seconds % 60

        months: int = self.year * 12 + self.month
        if months < 0:
            self.year = int((months - 11) / 12)
        else:
            self.year = months // 12
        self.month = months - self.year * 12

    @property
    def years(self) -> int:
        nft: freetime = self.copy()
        nft.sim()
        return nft.year

    @property
    def months(self) -> int:
        nft: freetime = self.copy()
        nft.sim()
        return nft.year * 12  +nft.month

    @property
    def days(self) -> int:
        nft: freetime = self.copy()
        nft.sim()
        return nft.day

    @property
    def hours(self) -> int:
        nft: freetime = self.copy()
        nft.sim()
        return nft.day * 24 + nft.hour

    @property
    def minutes(self) -> int:
        nft: freetime = self.copy()
        nft.sim()
        return nft.day * 24 * 60 + nft.hour * 60 + nft.minute

    @property
    def seconds(self) -> int:
        nft: freetime = self.copy()
        nft.sim()
        return nft.day * 86400 + nft.hour * 3600 + nft.minute * 60 + nft.second

    @property
    def mseconds(self) -> int:
        raise NotImplementedError

    def is_empty(self) -> bool:
        for val in self._values:
            if val != 0:
                return True
        return False
    
    def is_positive(self) -> int:
        if self.is_empty():
            return False
        return self.months >= 0 and self.seconds >= 0  # note | Not precise in fact @2024-04-09 10:45:04


class realtime(_time):

    values_default = (1900, 1, 1, 0, 0, 0, 0)

    def __init__(self, year: int = -1, month: int = -1, day: int = -1, hour: int = -1, minute: int = -1, second: int = -1, msecond: int = -1):
        _time.__init__(self, year, month, day, hour, minute, second, msecond)
        self._timescale = realevel.UNKNOWN
        self.check()

    def __copy__(self):
        return realtime(self.year, self.month, self.day, self.hour, self.minute, self.second, self.msecond)

    def __str__(self):
        rst: str = str(self.year)
        if self.timescale == realevel.YEAR:
            return rst
        
        rst += "/" + str(self.month)
        if self.timescale == realevel.MONTH:
            return rst
        
        rst += "/" + str(self.day)
        if self.timescale == realevel.DAY:
            return rst

        rst += " " + str(self.hour)
        if self.timescale == realevel.HOUR:
            return rst

        rst += ":" + str(self.minute)
        if self.timescale == realevel.MINUTE:
            return rst

        rst += ":" + str(self.second)
        if self.timescale == realevel.SECOND:
            return rst
        
        raise ShouldNeverSeeError(f"{self.timescale=}")

    def __repr__(self):
        return self.__str__()


    def __gt__(self, rt2: realtime):
        if not isinstance(rt2, realtime):
            raise TypeError
        
        for i in range(7):
            if self._values[i] <= rt2._values[i]:
                return False
        return True

    def __lt__(self, rt2: realtime):
        if not isinstance(rt2, realtime):
            raise TypeError
        
        for i in range(7):
            if self._values[i] >= rt2._values[i]:
                return False
        return True

    def __ge__(self, rt2: realtime):
        if not isinstance(rt2, realtime):
            raise TypeError
        
        for i in range(7):
            if self._values[i] < rt2._values[i]:
                return False
        return True

    def __le__(self, rt2: realtime):
        if not isinstance(rt2, realtime):
            raise TypeError
        
        for i in range(7):
            if self._values[i] > rt2._values[i]:
                return False
        return True

    def __eq__(self, rt2: realtime):
        if not isinstance(rt2, realtime):
            raise TypeError
        
        for i in range(7):
            if self._values[i] != rt2._values[i]:
                return False
        return True

    def __ne__(self, rt2: realtime):
        return not (self == rt2)
    
    
    
    def __iadd__(self, ft2: freetime):
        assert isinstance(ft2, freetime)
        for i in range(len(self._values)):
            if self.timescale.value >= i:
                self._values[i] += ft2._values[i]
            else:
                break
        self.sim()
        return self
    
    def __add__(self, ft2: freetime):
        assert isinstance(ft2, freetime)
        ftN = self.copy()
        ftN += ft2
        return ftN

    
    def __isub__(self, ft2: freetime):
        if isinstance(ft2, freetime):
            for i in range(len(self._values)):
                if self.timescale.value >= i:
                    self._values[i] -= ft2._values[i]
                else:
                    break
            self.sim()
            return self
        else:
            raise TypeError

    def __sub__(self, ft2: _time):
        if isinstance(ft2, freetime):
            ftN = self.copy()
            ftN -= ft2
            return ftN
        elif isinstance(ft2, realtime):
            assert self.timescale == ft2.timescale
            stamp1 = self.stamp
            stamp2 = ft2.stamp
            if stamp1 == stamp2:
                return freetime()
            return freetime(**{self.timescale.name.lower(): (stamp1-stamp2)})
        else:
            raise TypeError


    def add(self, ft2: freetime):
        self += ft2
        return self
    
    def sub(self, ft2: freetime):
        self -= ft2
        return self

    
    def copy(self):
        return self.__copy__()

    @property
    def timescale(self):
        if self._timescale != realevel.UNKNOWN:
            return self._timescale
        
        # logger.debug(f"in timescale: {self._values=}")

        for i in range(len(self._values)):
            if self._values[i] < 0:
                self._timescale = realevel(i-1) 
                return self._timescale

        self._timescale = realevel.MSECOND
        return self._timescale
    
    def check(self, ts: realevel = realevel.ALL):
        from ._x_time import Time
        assert self.timescale != realevel.UNKNOWN

        assert ts.value <= self.timescale.value

        # logger.debug(f"{ts=}, {self.timescale=} for {self}")

        if (ts == realevel.MONTH or ts == realevel.ALL and self.timescale >= realevel.MONTH) and self.month <= 0 or self.month > 12:
            raise RuntimeError(f"Wrong month: {self.month}")
        if (ts == realevel.DAY or ts == realevel.ALL and self.timescale >= realevel.DAY):
            if self.day <= 0 or self.day > Time.get_days_from_ym(self.year, self.month):
                raise RuntimeError(f"Wrong day: {self.day} in {self.year}{self.month}")
        if (ts == realevel.HOUR or ts == realevel.ALL and self.timescale >= realevel.HOUR) and self.hour < 0 or self.hour > 23:
            raise RuntimeError(f"Wrong hour: {self.hour}")
        if (ts == realevel.MINUTE or ts == realevel.ALL and self.timescale >= realevel.MINUTE) and self.minute < 0 or self.minute > 59:
            raise RuntimeError(f"Wrong minute: {self.minute}")
        if (ts == realevel.SECOND or ts == realevel.ALL and self.timescale >= realevel.SECOND) and self.second < 0 or self.second > 59:
            raise RuntimeError(f"Wrong second: {self.second}")
        if (ts == realevel.MSECOND or ts == realevel.ALL and self.timescale >= realevel.MSECOND) and self.msecond < 0 or self.msecond > 999:
            raise RuntimeError(f"Wrong msecond: {self.msecond}")

    @property
    def year(self):
        return self._values[0]

    @year.setter
    def year(self, val: int):
        self._values[0] = val
        self._timescale = realevel.UNKNOWN
        self.check(realevel.YEAR)
    
    def set_year(self, val: int):
        self.year = val
        return self

    @property
    def month(self):
        return self._values[1]

    @month.setter
    def month(self, val: int):
        self._values[1] = val
        if self.timescale.value < realevel.YEAR.value:
            raise RuntimeError("set time across multiple levels")
        self._timescale = realevel.UNKNOWN
        self.check(realevel.MONTH)
    
    def set_month(self, val: int):
        self.month = val
        return self

    @property
    def day(self):
        return self._values[2]

    @day.setter
    def day(self, val: int):
        self._values[2] = val
        if self.timescale.value < realevel.MONTH.value:
            raise RuntimeError("set time across multiple levels")
        self._timescale = realevel.UNKNOWN
        self.check(realevel.DAY)
    
    def set_day(self, val: int):
        self.day = val
        return self

    @property
    def hour(self):
        return self._values[3]

    @hour.setter
    def hour(self, val: int):
        self._values[3] = val
        if self.timescale.value < realevel.DAY.value:
            raise RuntimeError("set time across multiple levels")
        self._timescale = realevel.UNKNOWN
        self.check(realevel.HOUR)
    
    def set_hour(self, val: int):
        self.hour = val
        return self

    @property
    def minute(self):
        return self._values[4]

    @minute.setter
    def minute(self, val: int):
        self._values[4] = val
        if self.timescale.value < realevel.HOUR.value:
            raise RuntimeError("set time across multiple levels")
        self._timescale = realevel.UNKNOWN
        self.check(realevel.MINUTE)
    
    def set_minute(self, val: int):
        self.minute = val
        return self

    @property
    def second(self):
        return self._values[5]

    @second.setter
    def second(self, val: int):
        self._values[5] = val
        if self.timescale.value < realevel.MINUTE.value:
            raise RuntimeError("set time across multiple levels")
        self._timescale = realevel.UNKNOWN
        self.check(realevel.SECOND)
    
    def set_second(self, val: int):
        self.second = val
        return self

    @property
    def msecond(self):
        return self._values[6]

    @msecond.setter
    def msecond(self, val: int):
        self._values[6] = val
        if self.timescale.value < realevel.SECOND.value:
            raise RuntimeError("set time across multiple levels")
        self._timescale = realevel.UNKNOWN
        self.check(realevel.MSECOND)
    
    def set_msecond(self, val: int):
        self.msecond = val
        return self

    @property
    def years(self) -> int:
        return self.year

    @property
    def months(self) -> int:
        return (self.year - 1) * 12  + self.month

    @property
    def days(self) -> int:
        from ._x_time import Time
        rst_days = self.day
        if self.year > 1:
            rst_days += ((self.year - 1) * 365 + Time.countLeap(1, self.year - 1, True, False))
        rst_days += Time.get_jdays(self.month, 1, self.year) - 1
        return rst_days

    @property
    def hours(self) -> int:
        return (self.days - 1) * 24 + self.hour


    @property
    def minutes(self) -> int:
        return self.hours * 60 + self.minute

    @property
    def seconds(self) -> int:
        return self.minutes * 60 + self.second

    @property
    def mseconds(self) -> int:
        raise NotImplementedError

    @property
    def stamp(self) -> int:
        if self.timescale == realevel.YEAR:
            return self.years
        elif self.timescale == realevel.MONTH:
            return self.months
        elif self.timescale == realevel.DAY:
            return self.days
        elif self.timescale == realevel.HOUR:
            return self.hours
        elif self.timescale == realevel.MINUTE:
            return self.minutes
        elif self.timescale == realevel.SECOND:
            return self.seconds
        elif self.timescale == realevel.MSECOND:
            return self.mseconds
        raise ShouldNeverSeeError

    def sim(self):
        from ._x_time import Time
        assert self.timescale != realevel.UNKNOWN

        if self.timescale == realevel.YEAR:
            return

        #@ year-month-logic
        months = self.year * 12 + self.month
        if months <= 0:
            self._values[0] = int((months - 12) / 12)
        else:
            self._values[0] = int((months - 1) / 12)
        self._values[1] = months - self.year * 12
        assert self.month > 0 and self.month < 13

        if self.timescale == realevel.MONTH:
            return

        # logger.debug(f"enter sim for {self}, before set20")
        #@ exp | Use self._values below to avoid timescale check since we changed the empty timescale to 0 now
        for i in range(self.timescale.value+1, 7):
            self._values[i] = 0
        
        seconds = (self.day - 1) * 86400 + self.hour * 3600 + self.minute * 60 + self.second
        if seconds >= 0:
            self._values[2] = int(seconds / 86400)
        else:
            self._values[2] = int((seconds - 86399) / 86400)
        seconds -= self._values[2] * 86400
        self._values[3] = seconds // 3600
        seconds -= self._values[3] * 3600
        self._values[4] = seconds // 60
        self._values[5] = seconds % 60
        self._values[2] += 1

        #@ month-day-logic | build a bridge between year-month and day
        if self._values[2] <= 0:
            nyears_n2p = int(-self._values[2] / 366) + 1 #@ exp | years that makes day be positive
            ndays_n2p = nyears_n2p * 365 + Time.countLeap(self._values[0] - nyears_n2p, self._values[0], False if self._values[1] > 2 else True, True if self._values[1] > 2 else False)
            self._values[0] -= nyears_n2p
            self._values[2] += ndays_n2p
        
        nyears_p20 = int(self._values[2] / 366)
        if nyears_p20 > 0:
            ndays_p20 = nyears_p20 * 365 + Time.countLeap(self._values[0], self._values[0] + nyears_p20, False if self._values[1] > 2 else True, True if self._values[1] > 2 else False)
            self._values[0] += nyears_p20
            self._values[2] -= ndays_p20



        while self._values[2] > Time.get_days_from_ym(self._values[0], self._values[1]):
            self._values[2] -= Time.get_days_from_ym(self._values[0], self._values[1])
            self._values[1] += 1
            if self._values[1] == 0:
                self._values[1] = 12
                self._values[0] -= 1
                assert self._values[0] > 0
            elif self._values[1] == 13:
                self._values[1] = 1
                self._values[0] += 1

        for i in range(self.timescale.value+1, 7):
            self._values[i] = -1

        # logger.debug(f"leave sim for {self}")

    def rebase(self, ts: realevel, inplace: bool = False):
        if strict:
            if not isinstance(ts, realevel):
                raise TypeError
            if ts.value < 0:
                raise ValueError 

        if inplace:
            rst = self
        else:
            rst = self.copy()

        if ts <= self.timescale:
            for i in range(ts.value, 7):
                rst._values[i] = -1
        else:
            for i in range(self.timescale.value + 1, ts.value + 1):
                rst._values[i] = realtime.values_default[i]
        
        rst._timescale = realevel.UNKNOWN
        
        return rst

    def rebase2rts(self, ts: realevel):
        from ._x_time import Time

        rts = realtimeseries()
        if ts == self.timescale:
            rts.add(self)
        elif ts < self.timescale:
            rts.add(self.rebase(ts))
        else:
            if self.timescale == realevel.YEAR:
                for m in range(1, 12+1):
                    rts.add(realtime(self.year, m).rebase2rts(ts))
            elif self.timescale == realevel.MONTH:
                for d in range(1, Time.get_days_from_ym(self.year, self.month)+1):
                    rts.add(realtime(self.year, self.month, d).rebase2rts(ts))
            elif self.timescale == realevel.DAY:
                for h in range(24):
                    rts.add(realtime(self.year, self.month, self.day, h).rebase2rts(ts))
            elif self.timescale == realevel.HOUR:
                for m in range(60):
                    rts.add(realtime(self.year, self.month, self.day, self.hour, m).rebase2rts(ts))
            elif self.timescale == realevel.MINUTE:
                for s in range(60):
                    rts.add(realtime(self.year, self.month, self.day, self.hour, self.minute, s).rebase2rts(ts))
            else:
                raise ShouldNeverSeeError
        return rts

            

class realtimeseries:
    def __init__(self, *args):
        """
        realtimeseries()
        realtimeseries(rt1: realtime, rt2: realtime, [delta: freetime])
        realtimeseries(Sequence[realtime])
        """
        self.rts = []
        if len(args) == 0:
            return
    
        if len(args) == 1:
            if not isinstanceAll(rtlist, realtime):
                raise TypeError
            self.rts = list(args[0])
            return

        if len(args) == 2:
            rt1, rt2 = args
            delta = None
        elif len(args) == 3:
            rt1, rt2, delta = args
        else:
            raise TypeError

        if rt1 > rt2:
            raise ValueError
        if rt1.timescale != rt2.timescale:
            raise ValueError("Error! realtimeseries only works for realtime objects with the same timescale!")
        ts = rt1.timescale
        if delta is None:
            delta = freetime(**{ts.name.lower(): 1})
        elif rt1 + delta == rt1:
            raise ValueError

        rtT = rt1.copy()

        while rtT <= rt2:
            self.rts.append(rtT.copy())
            rtT += delta
        
        return

    
    @property
    def timescale(self):
        if not self.rts:
            return realevel.UNKNOWN
        else:
            return self.rts[0].timescale

    def add(self, rt1s: realtime | realtimeseries):
        if isinstance(rt1s, realtime):
            self.rts.append(rt1s)
        elif isinstance(rt1s, realtimeseries):
            self.rts.extend(rt1s.rts)
        else:
            raise TypeError
    
    def is_continuous(self):
        raise NotImplementedError