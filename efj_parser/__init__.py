import re
from typing import NamedTuple, Optional, Callable, Union, cast
import datetime as dt


class Duty(NamedTuple):
    start: dt.datetime  #: Start of duty
    duration: int  #: Length of duty in minutes
    ftl_correction: int = 0  #: Minutes to reduce duty length for FTL
    extra_flags: tuple[str, ...] = ()  #: Any unprocessed flags
    comment: str = ""  #: Remarks


class Crewmember(NamedTuple):
    role: str  #: The crewmember's role (e.g. CP, FO, PU, FA)
    name: str  #: The crewmember's name


class Roles(NamedTuple):
    p1: int = 0  #: Minutes operating as p1
    p1s: int = 0  #: Minutes operating as p1s
    p2: int = 0  #: Minutes operating as p2
    put: int = 0  #: Minutes operating as put
    instructor: int = 0  #: Minutes operating as instructor


class Conditions(NamedTuple):
    night: int = 0  #: Minutes operating at night
    ifr: int = 0  #: Minutes operating under IFR


class Landings(NamedTuple):
    day: int = 0  #: Number of day landings
    night: int = 0  #: Number of night landings


class Aircraft(NamedTuple):
    reg: str  #: The registration of the aircraft
    type_: str  #: The type of the aircraft
    class_: str = ""  #: Override to class based on type: spse, spme or mc


class Airports(NamedTuple):
    origin: str  #: The origin airport
    dest: str  #: The destination airport


class Sector(NamedTuple):
    start: dt.datetime  #: Off chocks date and time
    total: int  #: Minutes between off chocks and on chocks
    roles: Roles  #: Minutes operating in each role
    conditions: Conditions  #: Minutes operating in ifr and at night
    landings: Landings  #: Number of day and night landings
    aircraft: Aircraft  #: Type and registration of the aircraft
    airports: Airports  #: Origin and destination airports
    captain: str  #: Name(s) of captain(s), Self for oneself
    extra_flags: tuple[str, ...]  #: Any flags not processed by the parser
    comment: str  #: Remarks
    crew: tuple[Crewmember, ...]  #: A (possible empty) list of crew


class ValidationError(Exception):
    """An problem was found in the input data."""

    def __init__(self, line_number, message, problem_string):
        self.line_number = line_number
        """The 1-indexed line number where the problem was found."""
        self.message = message
        """A message describing the problem."""
        self.problem_string = problem_string
        """The string that caused the problem."""

    def __str__(self):
        return (f"Line {self.line_number}: "
                f"[{self.message}] {self.problem_string}")


class _VE(Exception):

    def __init__(self, message): self.message = message


ParseRet = Union[dt.date, Duty, Aircraft, list[Crewmember], Sector, str]
ParseHook = Optional[Callable[[str, int, str, ParseRet], None]]


class Parser():
    """Parser for electronic Flight Journal (eFJ) files."""
    def __init__(self) -> None:
        self.date: Optional[dt.date] = None
        self.airports = Airports("", "")
        self.aircraft = Aircraft("", "")
        self.captain = ""
        self.crewlist: list[Crewmember] = []

    def __parse_date(self, mo: re.Match) -> dt.date:
        try:
            self.date = dt.datetime.strptime(mo.group(1), "%Y-%m-%d")
            return self.date
        except ValueError:
            raise _VE("Incorrect Date entry")

    def __parse_nextdate(self, mo: re.Match) -> dt.date:
        if not self.date:
            raise _VE("Short date without preceding Date entry")
        self.date += dt.timedelta(len(mo.group(1)))
        return self.date

    def __parse_duty(self, mo: re.Match) -> Duty:
        if not self.date:
            raise _VE("Duty entry without preceding Date entry")
        try:
            t_start = dt.datetime.strptime(mo.group(1), '%H%M').time()
            t_end = dt.datetime.strptime(mo.group(2), '%H%M').time()
        except ValueError:
            raise _VE("Invalid time string")
        dt_start = dt.datetime.combine(self.date, t_start)
        dt_end = dt.datetime.combine(self.date, t_end)
        if dt_end < dt_start:
            dt_end += dt.timedelta(days=1)
        duration = int((dt_end - dt_start).total_seconds() / 60)
        flags = tuple(X.strip() for X in mo.group(3).split())
        ftl_correction = 0
        unused_flags = []
        for f in flags:
            if f and (mo_cor := re.match(r"r(:\d+)?", f)):
                if mo_cor.group(1):
                    ftl_correction = int(mo_cor.group(1)[1:])
                else:
                    ftl_correction = duration
            else:
                unused_flags.append(f)
        comment = mo.group(4)[1:].strip() if mo.group(4) else ""
        return Duty(dt_start, duration, ftl_correction,
                    tuple(unused_flags), comment)

    def __parse_aircraft(self, mo: re.Match) -> Aircraft:
        self.aircraft = Aircraft(mo.group(1).strip(), mo.group(2).strip())
        return self.aircraft

    def __parse_crewlist(self, mo: re.Match) -> list[Crewmember]:
        self.crewlist = []
        try:
            crew = mo.group(1).strip()
            if not crew:
                return []
            for role, name in [X.strip().split(":", 1)
                               for X in crew.split(",")]:
                role = role.strip()
                if not role or " " in role:
                    raise ValueError
                name = " ".join([X.strip() for X in name.split()])
                if not name or ":" in name:
                    raise ValueError
                self.crewlist.append(Crewmember(role, name))
        except ValueError:
            raise _VE("Incorrect crew listing format")
        captains = [X.name for X in self.crewlist if X.role == "CP"]
        if captains:
            self.captain = ", ".join(captains)
        return self.crewlist

    def __pre_validate_sector(self, mo: re.Match) -> None:
        if not self.date:
            raise _VE("Sector with no preceding Date entry")
        if not (self.aircraft.reg and self.aircraft.type_):
            raise _VE("Sector with no preceding Aircraft entry")
        if not mo.group(1) and not self.airports.dest:  # Blank destination
            raise _VE("Blank From without previous To")
        if not mo.group(2) and not self.airports.origin:  # Blank origin
            raise _VE("Blank To without previous From")

    def __parse_sector(self, mo: re.Match) -> Sector:
        self.__pre_validate_sector(mo)
        self.airports = Airports(mo.group(1) or self.airports.dest,
                                 mo.group(2) or self.airports.origin)
        try:
            ts = dt.datetime.strptime(mo.group(3), '%H%M').time()  # Off blocks
            te = dt.datetime.strptime(mo.group(4), '%H%M').time()  # On blocks
        except ValueError:
            raise _VE("Incorrect time field")
        flags = tuple(mo.group(5).split())
        start = dt.datetime.combine(cast(dt.date, self.date), ts)
        duration = int(
            (dt.datetime.combine(cast(dt.date, self.date), te) - start)
            .total_seconds() // 60)
        if duration < 0:
            duration += 1440
        conditions, unused_flags = _process_conditions(flags, duration)
        roles, unused_flags = _process_roles(unused_flags, duration)
        if roles.p2 == duration:
            landings = Landings()
        else:
            landings, unused_flags = _process_landings(unused_flags, duration,
                                                       conditions.night)
        aircraft_class, unused_flags = _process_class_override(unused_flags)
        if roles.p1 == duration:
            self.captain = "Self"
        else:
            if not self.captain:
                raise _VE("No Captain specified")
            if roles.p1:
                self.captain = f"Self, {self.captain}"
        comment = ""
        if mo.group(6):  # Comment
            comment = mo.group(6)[1:].strip()
        return Sector(
            start,
            duration,
            roles,
            conditions,
            landings,
            self.aircraft._replace(class_=aircraft_class),
            self.airports,
            self.captain,
            unused_flags,
            comment,
            tuple(self.crewlist))

    def __parse_comment(self, mo: re.Match) -> str:
        return mo.group(1) or ""

    def __invalid_syntax(self, mo: re.Match) -> None:
        raise _VE("Bad syntax")

    def parse(self, s: str, hook: ParseHook = None
              ) -> tuple[tuple[Duty, ...], tuple[Sector, ...]]:
        """Extract duties and sectors from an eFJ string

        :param s: A string containing data in eFJ format
        :param hook: A function that, if specified, will be called after each
            line is processed. The function will be called with the positional
            parameters line text, line number, line type and parsed object.
            Line type may be "blank", "comment", "date", "short_date",
            "aircraft", "crewlist" or "sector".
        :return: Two tuples containing the extracted data. The first is a tuple
            of Duty structures and the second is a tuple of Sector structures.

        """
        duties: list[Duty] = []
        sectors: list[Sector] = []
        func_map = [
            (re.compile(r"\A#(.*)\Z"),
             self.__parse_comment, "comment"),
            (re.compile(r"\A(\d{4}-\d{2}-\d{2})\Z"),
             self.__parse_date, "date"),
            (re.compile(r"\A\s*(\++)\s*\Z"),
             self.__parse_nextdate, "short_date"),
            (re.compile(r"\A(\d{4})/(\d{4})([^#]*)(#.+)?\Z"),
             self.__parse_duty, "duty"),
            (re.compile(r"([-\w]{2,10})\s*:\s*([-\w]+)"),
             self.__parse_aircraft, "aircraft"),
            (re.compile(r"\{([^}]*)}\Z"),
             self.__parse_crewlist, "crewlist"),
            (re.compile(r"(\w+)?/(\w+)?\s*(\d{4})/(\d{4})([^#]*)?(#.+)?"),
             self.__parse_sector, "sector"),
            (re.compile(r".+"),
             self.__invalid_syntax, "invalid"),
        ]
        for c, line in enumerate(s.splitlines()):
            line = line.strip()
            if not line:
                hook and hook(line, c, 'blank', "")
                continue
            ret = None
            for rexp, func, entry_type in func_map:
                if mo := rexp.match(line):
                    try:
                        ret = func(mo)
                    except _VE as e:
                        raise ValidationError(c + 1, e.message, mo.group(0))
                    hook and hook(line, c + 1, entry_type, cast(ParseRet, ret))
                    break
            if isinstance(ret, Duty):
                duties.append(ret)
            elif isinstance(ret, Sector):
                sectors.append(ret)
        return (tuple(duties), tuple(sectors))


def _process_landings(
        flags: tuple[str, ...],
        duration: int,
        night: int
) -> tuple[Landings, tuple[str, ...]]:
    night_ldg, day_ldg = 0, 0
    found_landing_flag = False
    re_day = re.compile(r"\Ald(:\d+)?\Z")
    re_night = re.compile(r"\Aln(:\d+)?\Z")
    unused = []
    for f in flags:
        if f == "m":
            night_ldg, day_ldg = 0, 0
            found_landing_flag = True
            break
        if mo := re_day.match(f):
            day_ldg = int(mo.group(1)[1:]) if mo.group(1) else 1
            found_landing_flag = True
        elif mo := re_night.match(f):
            night_ldg = int(mo.group(1)[1:]) if mo.group(1) else 1
            found_landing_flag = True
        else:
            unused.append(f)
    if not found_landing_flag:
        if duration == night:
            night_ldg = 1
        else:
            day_ldg = 1
    return Landings(day_ldg, night_ldg), tuple(unused)


def _process_roles(
        flags: tuple[str, ...],
        duration: int
) -> tuple[Roles, tuple[str, ...]]:
    """Extract role durations from flags

    :param flags: Sector flags
    :return: A Roles object and the flags input parameter with processed flags
        removed.
    """
    p1, inst = duration, 0
    roles = [0, 0, 0, 0]
    re_role = re.compile(r"\A(p1s|p2|put|p0)(:\d+)?\Z")
    re_inst = re.compile(r"\A(ins)(:\d+)?\Z")
    unused: list[str] = []
    for f in flags:
        if mo := re_role.match(f):
            idx = ("p1s", "p2", "put", "p0").index(mo.group(1))
            roles[idx] = int(mo.group(2)[1:]) if mo.group(2) else duration
            p1 -= roles[idx]
            if p1 < 0:
                raise _VE("Too many roles")
        elif mo := re_inst.match(f):
            inst = int(mo.group(2)[1:]) if mo.group(2) else duration
        else:
            unused.append(f)
    return Roles(p1, roles[0], roles[1], roles[2], inst), tuple(unused)


def _process_conditions(
        flags: tuple[str, ...], duration: int
) -> tuple[Conditions, tuple[str, ...]]:
    """Processes sector condition flags

    :param flags: The flags as a tuple of strings
    :return: A tuple of the form (Conditions, unused_flags) where unused flags
        is the input tuple with used flags removed.
    """
    night, vfr = 0, 0
    unused: list[str] = []
    re_flag = re.compile(r"\A(n|v)(:\d+)?\Z")
    for f in flags:
        mo = re_flag.match(f)
        if not mo:
            unused.append(f)
            continue
        if mo.group(1) == "n":
            night = duration
            if mo.group(2):
                night = int(mo.group(2)[1:])
                if night > duration:
                    raise _VE("Night duration more than flight duration")
        elif mo.group(1) == "v":
            vfr = duration
            if mo.group(2):
                vfr = int(mo.group(2)[1:])
                if vfr > duration:
                    raise _VE("VFR duration more than flight duration")
    return Conditions(night, duration - vfr), tuple(unused)


def _process_class_override(
        flags: tuple[str, ...]
) -> tuple[str, tuple[str, ...]]:
    retval = ""
    unused = []
    for f in flags:
        if f in {"spse", "spme", "mc"}:
            retval = f
        else:
            unused.append(f)
    return retval, tuple(unused)
