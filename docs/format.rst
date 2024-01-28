Format Description
==================

Overview
--------

An Electronic Flight Journal (EFJ) is a simple text file within which your
flying records are stored in a non-tabular form. If you ponder for a minute how
you might efficiently record your flying records in a pocket diary, you will
likely come up with a paper based version of the scheme. It is a useful format
in and of itself, and, using this parser, it is easy to generate other formats,
including FCL.050 compliant logbooks — I have provided a tool (with a web
version for those who prefer) that does just this.

Since an EFJ is just a text file, it can be read and edited with any and all of
the myriad of text editors that are available on each and every platform. There
is zero probability that the file will become unusable in the future as a
result of a tech company losing interest in maintaining a particular bit of
software.

The file size of an EFJ is very small — my 15,000 hours of flying result in an
uncompressed 365KB file or a compressed 75KB file — which makes it trivial to
widely distribute copies to insure against loss due to hardware failure.

For easyJet pilots there is also a tool (again with an online version) that
turns a downloaded AIMS roster directly into a set of EFJ entries. This makes
management of your flight records almost effortless.

Pilots from other airlines that use AIMS for rostering *may* (assuming the
detailed roster that they can download is sufficiently similar to the easyJet
version) also find this tool useful, although they will have to manually insert
the details of the aircraft they were operating. Hopefully, suitably skilled
pilots at other airlines will be able to fork this tool and provide their
colleagues with a similarly effortless experience.


Top Level Structure
-------------------

Blank lines and lines starting with ``#`` are ignored to allow spacing and
comments as desired.

Otherwise, each line must be one of a:

    * Date
    * Duty
    * Aircraft
    * Crew
    * Sector

To minimise typing while still remaining human readable, context carries
forwards (e.g. a Date applies to all Duties and Sectors until another Date
replaces it) and the most common options are specified by omission.

As an example, a couple of days of a Captain's flying, including both optional
crew and duty records, might look like this: ::

    2024-01-23
    1000/1500
    {FO:Bloggs, PU:Smith}
    G-ABCD:A320
    BRS/BFS 1100/1200  # Bird strike
    / 1330/1430
    # A general comment about the day

    +
    1100/1545
    {FO:Jones, PU:McDonald}
    G-EFGH:A321
    BRS/CDG 1200/1315
    / 1400/1515

Date
----

A Date is either an iso format date: ::

    2024-01-23

or a short form consisting of one or more + characters: ::

    ++

In the latter case, the date is moved on one day for each ``+`` — a
full date must have been specified before this form is used.

Duty
----

Two UTC times, each consisting of four digits, separated by a forward slash,
followed by zero or more flags, followed by an optional comment preceded by a
``#`` character. For example: ::

    0500/1100 r:30  # ESBY

The only flag currently specified is ``r``. On its own, it means do not include
the duty time in cumulative FTL duty limit calculations. If followed by a colon
and an integer, as shown above, the integer is the number of minutes to not
include. In the above example, the duty would contribute 5 hours 30 minutes to
cumulative duty calculations.

The main reason for this flag is an FTL clause regarding early standby duties
that do not result in a call out; any time spent on such a standby that occurs
in the period 22:00 to 08:00 local time in the crew member's acclimatised
timezone only counts half towards cumulative duty totals. It is not possible to
infer the correct timezone from the available data, so a manual correction is
required.

It can also be used to correct for High Contactable time on duty if you wish to
record these as they do not count towards cumulative duty at all.

Aircraft
--------

Registration and type separated by a colon: ::

    G-ABCD:A320

These may be any combination of letters, numbers or hyphens.

Crew
----

A list of crew in the form **role : name**, separated by commas, with the
entire group enclosed in curly braces. Only the role ``CP`` has meaning to the
parser -- other roles such as ``FO``, ``PU`` and ``FA`` may have meaning to
report generating software. Multiple entries can have the same role.

For example: ::

    { CP:Bloggs Joe, PU:Jones, FA:McDonald, FA: Smith }

An empty set of braces can be used if you want to prevent previous
crews being carried forward: ::

    { }

Sector
------

Origin and destination airport (without spaces — use an underscore if
necessary), separated by a forward slash, followed by two UTC times, each
consisting of four digits, again separated by a forward slash, followed by zero
of more flags, then an optional comment preceded by a ``#`` character. For
example: ::

    BRS/BFS 1000/1100 p1s  # Bird strike

Except for the first sector being processed, the origin and/or destination
airport may be omitted. If the origin is omitted, the value of the previous
destination is used, and vice versa. For example: ::

    BRS/BFS 1000/1100 p1s  # Bird strike
    / 1200/1300 p2

is equivalent to: ::

    BRS/BFS 1000/1100 p1s  # Bird strike
    BFS/BRS 1200/1300 p2

Night flag
~~~~~~~~~~~

An ``n`` flag indicates that the whole flight took place at night. If only part
of the flight took place at night, add a colon followed by an integer, where
the integer is the number of minutes to consider as night flying, e.g. ``n:30``
would mean 30 minutes of the flight were night flying and the rest was day.

If only part of a flight took place at night, it is difficult to infer whether
the landing was during the day or night part. Use an ``ln`` flag to indicate
that it was at night, otherwise it is assumed to have been during the day. For
example: ::

    BRS/SSH 1600/2000 n:120 ln
    / 2100/0100 n

Role flags
~~~~~~~~~~

The possible role flags are ``p1s``, ``p2``, ``put`` and ``ins``. Each of these
may optionally be followed by a colon and an integer to specify the number of
minutes of the flight that were operated in that role. A role flag without a
colon or integer is equivalent to one with the colon and an integer
representing the entire duration of the flight, e.g. for a 60 minute flight,
``p1s`` is equivalent to ``p1s:60``.

Any minutes not assigned as ``p1s``, ``p2`` and/or ``put``, are assumed to be
operated as p1, so Captains just need to omit these flags. The ``ins`` flag is
for recording that you were operating as an instructor.

Examples: ::

  BRS/CDG 1600/1700  # operating as p1 throughout the flight
  BRS/CDG 1600/1700 p1s  # operating as p1s throughout the flight
  BRS/CDG 1600/1700 p2:30 p1s:30  # operating as p1s for half the flight
  BRS/CDG 1600/1700 ins  # operating as instructor

Flight rule flag
~~~~~~~~~~~~~~~~

Use a ``v`` flag to record that the flight was operated under visual flight
rules. If omitted, flight under instrument flight rules is assumed. ::

    BRS/BRS 1000/1100 v

If only part of the flight was operated under visual flight rules, add a colon
and the integer value of VFR minutes. For example if you cancelled IFR after 30
minutes, the above sector would be written: ::

    BRS/BRS 1000/1100 v:30


Landing overrides
~~~~~~~~~~~~~~~~~

The landing override flags are ``ld`` for day landings and ``ln`` for night
landings. To specify multiple landings use a colon followed by an integer, i.e.
``ld:3`` means three day landings. ``ld`` is equivalent to ``ld:1`` and ``ln``
is equivalent to ``ln:1``. Both flags may be specified. ``ld:2 ln`` means two
day landings and one night landing.

If, and only if, neither flag is used, a single day landing will be assumed if
a flight took place entirely in daytime and a single night landing will be
assumed if a flight took place entirely at nighttime. If only part of the
flight took place at night, a day landing is assumed. Thus an ``ln`` flag must
be used if part of a flight took place at night and the landing was a night
landing.

No check is made for reasonableness. If an ``ld`` flag is used when the flight
took place entirely at night, one day landing will still be recorded.

To specify that you were not involved in the landing, use either ``ld:0`` or
``ln:0`` as you see fit.

Examples: ::

  EMA/EMA 1000/1100  # 1 day landing assumed
  EMA/EMA 2200/2300 n  # 1 night landing assumed
  EMA/FNC 0600/0900 n:60  # 1 day landing assumed
  FNC/EMA 1800/2100 n:120 ln  # 1 night landing (must be specified)
  EMA/EMA 1000/1100 put ld:5  # 5 training circuits
  EMA/EMA 2100/2300 n:60 ld:5 ln:4  # 5 day circuits then 4 night circuits
  EMA/EMA 1000/1300 ins ld:10  # 10 day landings as instructor
  EMA/FNC 1000/1300 ld:0  # Zero landings for some reason

Aircraft class overrides
~~~~~~~~~~~~~~~~~~~~~~~~

Whether a flight is single-pilot, single-engine; single-pilot, multi-engine; or
multi-crew will usually be inferred from the type of aircraft being flown. In
very rare cases, this might need to be over-ridden on a sector by sector basis,
in which case the flags ``spse``, ``spme`` or ``mc`` respectively can be used.

Unknown flags
~~~~~~~~~~~~~

Any flags that are not processed by the parser can be found in the ``extra
flags`` field of the Sector object. This is to allow flags that may be
meaningful to a tool using the parser but not to the parser itself to be passed
on.
