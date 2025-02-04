import unittest
import datetime as dt

import efj_parser as efj


class TestRegexp(unittest.TestCase):

    def test_shortdate(self):
        f = efj.Parser._Parser__RE_SHORTDATE.fullmatch
        # Next day
        self.assertEqual(f("+").group(1), "+")
        # Next next next day
        self.assertEqual(f("+++").group(1), "+++")
        # Can only be +
        self.assertIsNone(f("++-+"))
        # Empty gives None
        self.assertIsNone(f(""))

    def test_date(self):
        f = efj.Parser._Parser__RE_DATE.fullmatch
        self.assertEqual(f("2025-01-01").group(1), "2025-01-01")
        # Must be ISO format
        self.assertIsNone(f("01/01/2025"))
        # Bad dates are OK -- will be detected when processing
        self.assertEqual(f("2025-21-01").group(1), "2025-21-01")
        # Can't be anything on the end
        self.assertIsNone(f("2025-01-01A"))
        # ... or the start
        self.assertIsNone(f("A2025-01-01"))
        # Dashes are mandatory
        self.assertIsNone(f("20250101"))
        # Empty gives None
        self.assertIsNone(f(""))

    def test_aircraft(self):
        f = efj.Parser._Parser__RE_AIRCRAFT.fullmatch
        for class_ in ["mc", "spse", "spme"]:
            self.assertEqual(
                f("G-ABCD:A320:" + class_).group(1, 2, 3),
                ("G-ABCD", "A320", class_)
            )
        # Other classes are no good
        self.assertIsNone(f("G-ABCD:A320:mcme"))
        # No class is fine
        self.assertEqual(
            f("G-ABCD:A320").group(1, 2, 3),
            ("G-ABCD", "A320", None)
        )
        # ... although trailing colon not allowed
        self.assertIsNone(f("G-ABCD:A320:"))
        # Space around colons is fine
        self.assertEqual(
            f("G-ABCD : A320 : mc").group(1, 2, 3),
            ("G-ABCD", "A320", "mc")
        )
        # Empty gives None
        self.assertIsNone(f(""))

    def test_comment(self):
        f = efj.Parser._Parser__RE_COMMENT.fullmatch
        self.assertEqual(f("# my comment").group(1), " my comment")
        # Multiple #
        self.assertEqual(f("## my #comment").group(1), "# my #comment")
        # Empty comment
        self.assertEqual(f("#").group(1), "")
        # Empty
        self.assertIsNone(f(""))

    def test_crew(self):
        f = efj.Parser._Parser__RE_CREWLIST.fullmatch
        self.assertEqual(f("{ cp: Pugwash, fo: Bloggs}").group(1),
                         " cp: Pugwash, fo: Bloggs")
        # Double close shouldn't match
        self.assertIsNone(f("{ cp: Pugwash, fo: Bloggs}}"))
        # Otherwise pretty much anything goes -- errors detected later
        self.assertEqual(f("{{sdkfjl cp: :fo}").group(1),
                         "{sdkfjl cp: :fo")
        # Empty
        self.assertIsNone(f(""))

    def test_duty(self):
        f = efj.Parser._Parser__RE_DUTY.fullmatch
        # just times
        self.assertEqual(f("1000/1100").group(1, 2, 3, 4),
                         ("1000", "1100", None, None))
        # with a comment
        self.assertEqual(f("1000/1100#test").group(1, 2, 3, 4),
                         ("1000", "1100", None, "test"))
        # with flags
        self.assertEqual(f("1000/1100 r a:10").group(1, 2, 3, 4),
                         ("1000", "1100", "r a:10", None))
        # comment and flags
        self.assertEqual(f("1000/1100 r:30 # test").group(1, 2, 3, 4),
                         ("1000", "1100", "r:30 ", " test"))
        # empty
        self.assertIsNone(f(""))
        # flag without space
        self.assertIsNone(f("1000/1100r "))
        # times with suffix
        self.assertIsNone(f("1000z/1100z "))
        # letters
        self.assertIsNone(f("abcd/efgh"))

    def test_sector(self):
        f = efj.Parser._Parser__RE_SECTOR.fullmatch
        # simplest
        self.assertEqual(
            f("BRS/FNC 1000/1300").group(1, 2, 3, 4, 5, 6),
            ("BRS", "FNC", "1000", "1300", None, None))
        # flags
        self.assertEqual(
            f("BRS/FNC 1000/1300 n:30 m").group(1, 2, 3, 4, 5, 6),
            ("BRS", "FNC", "1000", "1300", "n:30 m", None))
        # comment
        self.assertEqual(
            f("BRS/FNC 1000/1300 #  test").group(1, 2, 3, 4, 5, 6),
            ("BRS", "FNC", "1000", "1300", None, "  test"))
        # flags and comment
        self.assertEqual(
            f("BRS/FNC 1000/1300 m#  test").group(1, 2, 3, 4, 5, 6),
            ("BRS", "FNC", "1000", "1300", "m", "  test"))
        # underscore
        self.assertEqual(
            f("my_house/FNC 1000/1300"). group(1, 2, 3, 4, 5, 6),
            ("my_house", "FNC", "1000", "1300", None, None))
        # no underscore
        self.assertIsNone(f("my house/FNC 1000/1300"))
        # time zones
        self.assertIsNone(f("BRS/FNC 1000z/1300z"))
        # empty
        self.assertIsNone(f(""))


class TestParser(unittest.TestCase):

    def test_basic(self):
        data = """\
2024-01-21
1000/1430
N1:320: mc
{FO: Bloggs}
BRS/BFS 1100/1200 ins #belfast
N2:320
/ 1300/1400 ins:20 test
{}
+
1000/1610  # Comment
OB-T-1274:A-321
/NCE 1100/1300 ld:3
/ 1340/1540 v:30 n:10 ln

++
0600/1200 r:60 test # ESBY
+
0600/0630 r # HCT
"""
        expected_duties = (
            efj.Duty(
                dt.datetime(2024, 1, 21, 10),
                270, 0, (), ""),
            efj.Duty(
                dt.datetime(2024, 1, 22, 10),
                370, 0, (), "Comment"),
            efj.Duty(
                dt.datetime(2024, 1, 24, 6),
                360, 60, ("test",), "ESBY"),
            efj.Duty(
                dt.datetime(2024, 1, 25, 6),
                30, 30, (), "HCT")
        )

        expected_sectors = (
            efj.Sector(
                dt.datetime(2024, 1, 21, 11), 60,
                efj.Roles(p1=60, instructor=60),
                efj.Conditions(ifr=60),
                efj.Landings(day=1),
                efj.Aircraft("N1", "320", "mc"),
                efj.Airports("BRS", "BFS"),
                "Self", (), "belfast",
                (efj.Crewmember("FO", "Bloggs"),)),
            efj.Sector(
                dt.datetime(2024, 1, 21, 13), 60,
                efj.Roles(p1=60, instructor=20),
                efj.Conditions(ifr=60),
                efj.Landings(day=1),
                efj.Aircraft("N2", "320", "mc"),
                efj.Airports("BFS", "BRS"),
                "Self", ("test",), "",
                (efj.Crewmember("FO", "Bloggs"),)),
            efj.Sector(
                dt.datetime(2024, 1, 22, 11), 120,
                efj.Roles(p1=120),
                efj.Conditions(ifr=120),
                efj.Landings(day=3),
                efj.Aircraft("OB-T-1274", "A-321", ""),
                efj.Airports("BRS", "NCE"),
                "Self", (), "", ()),
            efj.Sector(
                dt.datetime(2024, 1, 22, 13, 40), 120,
                efj.Roles(p1=120),
                efj.Conditions(night=10, ifr=90),
                efj.Landings(night=1),
                efj.Aircraft("OB-T-1274", "A-321", ""),
                efj.Airports("NCE", "BRS"),
                "Self", (), "", ()))
        self.assertEqual(
            efj.Parser().parse(data),
            (expected_duties, expected_sectors))

    def test_fo(self):
        data = """\
2024-01-21
1000/1430
G-ABCD:320
{CP:Bloggs Joe}
# A general comment about something
BRS/BFS 1100/1200 p1s #belfast
/ 1300/1400 p2

+++
1000/1610  # Comment
{CP:Pugwash, PU:Purser}
G-EFGH:321
/NCE 1100/1300 p2
/ 1340/1540 p1s:30
"""
        expected_duties = (
            efj.Duty(
                dt.datetime(2024, 1, 21, 10),
                270, 0, (), ""),
            efj.Duty(
                dt.datetime(2024, 1, 24, 10),
                370, 0, (), "Comment"))
        expected_sectors = (
            efj.Sector(
                dt.datetime(2024, 1, 21, 11), 60,
                efj.Roles(p1s=60),
                efj.Conditions(ifr=60),
                efj.Landings(day=1),
                efj.Aircraft("G-ABCD", "320", ""),
                efj.Airports("BRS", "BFS"),
                "Bloggs Joe", (), "belfast",
                (efj.Crewmember("CP", "Bloggs Joe"),)),
            efj.Sector(
                dt.datetime(2024, 1, 21, 13), 60,
                efj.Roles(p2=60),
                efj.Conditions(ifr=60),
                efj.Landings(),
                efj.Aircraft("G-ABCD", "320", ""),
                efj.Airports("BFS", "BRS"),
                "Bloggs Joe", (), "",
                (efj.Crewmember("CP", "Bloggs Joe"),)),
            efj.Sector(
                dt.datetime(2024, 1, 24, 11), 120,
                efj.Roles(p2=120),
                efj.Conditions(ifr=120),
                efj.Landings(),
                efj.Aircraft("G-EFGH", "321", ""),
                efj.Airports("BRS", "NCE"),
                "Pugwash", (), "", (
                    efj.Crewmember("CP", "Pugwash"),
                    efj.Crewmember("PU", "Purser"),)),
            efj.Sector(
                dt.datetime(2024, 1, 24, 13, 40), 120,
                efj.Roles(p1=90, p1s=30),
                efj.Conditions(ifr=120),
                efj.Landings(day=1),
                efj.Aircraft("G-EFGH", "321", ""),
                efj.Airports("NCE", "BRS"),
                "Self, Pugwash", (), "", (
                    efj.Crewmember("CP", "Pugwash"),
                    efj.Crewmember("PU", "Purser"),)),
        )
        self.assertEqual(
            efj.Parser().parse(data),
            (expected_duties, expected_sectors))

    def test_flags(self):
        aircraft = efj.Aircraft("G-ABCD", "320", "")
        roles = efj.Roles(p1=60)
        airports = efj.Airports("BRS", "BFS")
        with self.subTest("Instructor flag"):
            data = """\
2024-01-21
G-ABCD:320
BRS/BFS 1100/1200 ins
"""
            expected_sectors = (
                efj.Sector(
                    dt.datetime(2024, 1, 21, 11), 60,
                    roles._replace(instructor=60),
                    efj.Conditions(ifr=60),
                    efj.Landings(day=1),
                    aircraft, airports,
                    "Self", (), "", ()),
            )
            self.assertEqual(
                efj.Parser().parse(data),
                ((), expected_sectors))
        with self.subTest("VFR specified, no landing"):
            data = """\
2024-01-21
G-ABCD:320
BRS/Airborne 1100/1200 v ld:0
"""
            expected_sectors = (
                efj.Sector(
                    dt.datetime(2024, 1, 21, 11), 60,
                    roles,
                    efj.Conditions(),
                    efj.Landings(),
                    aircraft, airports._replace(dest="Airborne"),
                    "Self", (), "", ()),
            )
            self.assertEqual(
                efj.Parser().parse(data),
                ((), expected_sectors))
        with self.subTest("VFR at night with day landing"):
            data = """\
2024-01-21
G-ABCD:320
BRS/BFS 1100/1200 v n:30
"""
            expected_sectors = (
                efj.Sector(
                    dt.datetime(2024, 1, 21, 11), 60,
                    roles,
                    efj.Conditions(night=30),
                    efj.Landings(day=1),
                    aircraft, airports,
                    "Self", (), "", ()),
            )
            self.assertEqual(
                efj.Parser().parse(data),
                ((), expected_sectors))

    def test_bad_crewstring(self):
        with self.subTest("Just a string"):
            data = "{just a string}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Invalid crew list] {just a string}")
        with self.subTest("No name"):
            data = "2024-01-22\n{CP:, FO:Bloggs}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 2: [Invalid crew list] {CP:, FO:Bloggs}")
        with self.subTest("No comma"):
            data = "{ CP: Bloggs1 FO:Bloggs2}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Invalid crew list]"
                " { CP: Bloggs1 FO:Bloggs2}")
        with self.subTest("No colon"):
            data = "{just a, string}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Invalid crew list] {just a, string}")
        with self.subTest("Multi word role"):
            data = "{just a: string}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Invalid crew list] {just a: string}")

    def test_bad_date(self):
        data = "2024-02-30"
        with self.assertRaises(efj.ValidationError) as e:
            efj.Parser().parse(data)
        self.assertEqual(
            str(e.exception),
            "Line 1: [Invalid date format] 2024-02-30")

    def test_bad_nextdate(self):
        data = "2024-02-01\n++-"
        with self.assertRaises(efj.ValidationError) as e:
            efj.Parser().parse(data)
        self.assertEqual(
            str(e.exception),
            "Line 2: [Invalid syntax] ++-")

    def test_bad_duty(self):
        with self.subTest("No preceding date"):
            data = "1000/1100"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Prior date specifier required] 1000/1100")
        with self.subTest("Bad time format"):
            data = "2024-02-01\n2200/2400"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 2: [Invalid time format] 2200/2400")
        with self.subTest("Hyphen instead of slash"):
            data = "2024-02-01\n2200-2400"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 2: [Invalid syntax] 2200-2400")


class TestSectorFlags (unittest.TestCase):

    def test_landings(self):
        with self.subTest("No flags, day"):
            self.assertEqual(
                efj._process_landings((), 1, 0),
                (efj.Landings(day=1, night=0), ()))
        with self.subTest("PM, day"):
            self.assertEqual(
                efj._process_landings((("m", None),), 1, 0),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("No flags, night"):
            self.assertEqual(
                efj._process_landings((), 1, 1),
                (efj.Landings(day=0, night=1), ()))
        with self.subTest("PM, night"):
            self.assertEqual(
                efj._process_landings((("m", None),), 1, 1),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("Partial night, day landing"):
            self.assertEqual(
                efj._process_landings((), 2, 1),
                (efj.Landings(day=1, night=0), ()))
        with self.subTest("Partial night, night landing"):
            self.assertEqual(
                efj._process_landings((("ln", None),), 2, 1),
                (efj.Landings(day=0, night=1), ()))
        with self.subTest("Multiple day landings"):
            self.assertEqual(
                efj._process_landings((("ld", 2),), 2, 0),
                (efj.Landings(day=2, night=0), ()))
        with self.subTest("Multiple night landings"):
            self.assertEqual(
                efj._process_landings((("ln", 2),), 2, 1),
                (efj.Landings(day=0, night=2), ()))
        with self.subTest("Mix of landings, single"):
            self.assertEqual(
                efj._process_landings((("ln", None), ("ld", None)), 2, 1),
                (efj.Landings(day=1, night=1), ()))
        with self.subTest("Mix of landings, multi"):
            self.assertEqual(
                efj._process_landings((("ln", 2), ("ld", None)), 2, 1),
                (efj.Landings(day=1, night=2), ()))
        with self.subTest("Zero landings, day flag"):
            self.assertEqual(
                efj._process_landings((("ld", 0),), 2, 1),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("Zero landings, night flag"):
            self.assertEqual(
                efj._process_landings((("ln", 0),), 2, 1),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("Day landing, night flight"):
            # Assume that user did this for a reason
            self.assertEqual(
                efj._process_landings((("ld", None),), 2, 2),
                (efj.Landings(day=1, night=0), ()))

    def test_roles(self):
        with self.subTest("All p1"):
            self.assertEqual(
                efj._process_roles((), 1),
                (efj.Roles(p1=1), ()))
        with self.subTest("All p1s"):
            self.assertEqual(
                efj._process_roles((("p1s", None),), 1),
                (efj.Roles(p1s=1), ()))
        with self.subTest("All p2"):
            self.assertEqual(
                efj._process_roles((("p2", None),), 1),
                (efj.Roles(p2=1), ()))
        with self.subTest("All put"):
            self.assertEqual(
                efj._process_roles((("put", None),), 1),
                (efj.Roles(put=1), ()))
        with self.subTest("Split roles, put & p1"):
            self.assertEqual(
                efj._process_roles((("put", 1),), 2),
                (efj.Roles(p1=1, put=1), ()))
        with self.subTest("Split roles, p1s & p1"):
            self.assertEqual(
                efj._process_roles((("p1s", 1),), 2),
                (efj.Roles(p1=1, p1s=1), ()))
        with self.subTest("Split roles, p2 & p1"):
            self.assertEqual(
                efj._process_roles((("p2", 1),), 2),
                (efj.Roles(p1=1, p2=1), ()))
        with self.subTest("Split roles, p1s & put"):
            self.assertEqual(
                efj._process_roles((("p1s", 1), ("put", 1)), 2),
                (efj.Roles(p1s=1, put=1), ()))
        with self.subTest("Role duration > duration"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_roles((("p1s", 2),), 1)
                self.assertEqual(ve.exception.message, "Invalid role flags")
        with self.subTest("Two untimed roles"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_roles((("p1s", None), ("put", None)), 1)
            self.assertEqual(ve.exception.message, "Invalid role flags")
        with self.subTest("Instructor flag"):
            self.assertEqual(
                efj._process_roles((("ins", None),), 1),
                (efj.Roles(p1=1, instructor=1), ()))
        with self.subTest("Instructor flag, partial"):
            self.assertEqual(
                efj._process_roles((("ins", 1),), 2),
                (efj.Roles(p1=2, instructor=1), ()))
        with self.subTest("Unknown role"):
            self.assertEqual(
                efj._process_roles((("p3", None),), 2),
                (efj.Roles(p1=2), (("p3", None),)))

    def test_conditions(self):
        with self.subTest("No flags"):
            self.assertEqual(
                efj._process_conditions((), 1),
                (efj.Conditions(ifr=1, night=0), ()))
        with self.subTest("VFR flag"):
            self.assertEqual(
                efj._process_conditions((("v", None),), 1),
                (efj.Conditions(ifr=0, night=0), ()))
        with self.subTest("Night flag"):
            self.assertEqual(
                efj._process_conditions((("n", None),), 1),
                (efj.Conditions(ifr=1, night=1), ()))
        with self.subTest("VFR at night"):
            self.assertEqual(
                efj._process_conditions((("n", None), ("v", None)), 1),
                (efj.Conditions(ifr=0, night=1), ()))
        with self.subTest("Part VFR"):
            self.assertEqual(
                efj._process_conditions((("v", 1),), 2),
                (efj.Conditions(ifr=1, night=0), ()))
        with self.subTest("Part Night"):
            self.assertEqual(
                efj._process_conditions((("n", 1),), 2),
                (efj.Conditions(ifr=2, night=1), ()))
        with self.subTest("VFR duration > duration"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_conditions((("v", 2),), 1),
            self.assertEqual(ve.exception.message,
                             "Invalid flight condition flags")
        with self.subTest("Night duration > duration"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_conditions((("n", 2),), 1),
            self.assertEqual(ve.exception.message,
                             "Invalid flight condition flags")


class TestUtility(unittest.TestCase):

    def test_split_flags(self):
        res = tuple(efj._split_flags("  p2 put:20 ln:1 ins  "))
        exp = (("p2", None), ("put", 20), ("ln", 1), ("ins", None))
        self.assertEqual(res, exp)
        with self.assertRaises(ValueError):
            tuple(efj._split_flags("ln:1 ab:no"))

    def test_join_flags(self):
        res = efj._join_flags(
            (("p2", None), ("put", 20), ("ln", 1), ("ins", None))
        )
        exp = ("p2", "put:20", "ln:1", "ins")
        self.assertEqual(res, exp)


class TestPrivateMethods(unittest.TestCase):

    def test_parse_times(self):
        parser = efj.Parser()
        if __debug__:
            with self.assertRaises(AssertionError) as e:
                efj.Parser._Parser__parse_times(parser, "1000", "1100")
        parser.date = dt.date(2025, 1, 1)
        ret = efj.Parser._Parser__parse_times(parser, "1000", "1100")
        self.assertEqual(ret, (dt.datetime(2025, 1, 1, 10, 0), 60))
        ret = efj.Parser._Parser__parse_times(parser, "2300", "0100")
        self.assertEqual(ret, (dt.datetime(2025, 1, 1, 23, 0), 120))
        with self.assertRaises(efj._VE) as e:
            efj.Parser._Parser__parse_times(parser, "1000", "3100")
        self.assertEqual(e.exception.code, efj._VE.Code.BAD_TIME)
        if __debug__:
            with self.assertRaises(AssertionError) as e:
                efj.Parser._Parser__parse_times(parser, "abcd", "1100")
            with self.assertRaises(AssertionError) as e:
                efj.Parser._Parser__parse_times(parser, None, "1100")
        if not __debug__:
            with self.assertRaises(efj._VE) as e:
                efj.Parser._Parser__parse_times(parser, "abcd", "1100")
            self.assertEqual(e.exception.code, efj._VE.Code.BAD_TIME)
            with self.assertRaises(efj._VE) as e:
                efj.Parser._Parser__parse_times(parser, None, "1100")
            self.assertEqual(e.exception.code, efj._VE.Code.BAD_TIME)

    def test_parse_date(self):
        parser = efj.Parser()
        mo = efj.Parser._Parser__RE_DATE.fullmatch("2025-01-01")
        self.assertEqual(
            efj.Parser._Parser__parse_date(parser, mo),
            dt.date(2025, 1, 1))
        mo = efj.Parser._Parser__RE_DATE.fullmatch("2025-21-01")
        with self.assertRaises(efj._VE) as e:
            efj.Parser._Parser__parse_date(parser, mo)
        self.assertEqual(e.exception.code, efj._VE.Code.BAD_DATE)
        if __debug__:
            with self.assertRaises(AssertionError):
                efj.Parser._Parser__parse_date(parser, None)

    def test_nextdate(self):
        parser = efj.Parser()
        parser.date = dt.date(2024, 12, 31)
        mo = efj.Parser._Parser__RE_SHORTDATE.fullmatch("+")
        efj.Parser._Parser__parse_nextdate(parser, mo)
        self.assertEqual(parser.date, dt.date(2025, 1, 1))
        mo = efj.Parser._Parser__RE_SHORTDATE.fullmatch("+++")
        efj.Parser._Parser__parse_nextdate(parser, mo)
        self.assertEqual(parser.date, dt.date(2025, 1, 4))
        if __debug__:
            with self.assertRaises(AssertionError):
                efj.Parser._Parser__parse_nextdate(parser, None)

    def test_duty(self):
        parser = efj.Parser()
        parser.date = dt.date(2024, 12, 31)
        mo = efj.Parser._Parser__RE_DUTY.fullmatch("1000/1100")
        res = efj.Parser._Parser__parse_duty(parser, mo)
        expected = efj.Duty(dt.datetime(2024, 12, 31, 10, 0), 60)
        self.assertEqual(res, expected)
        mo = efj.Parser._Parser__RE_DUTY.fullmatch("1000/1100 r:30")
        res = efj.Parser._Parser__parse_duty(parser, mo)
        expected = expected._replace(ftl_correction=30)
        self.assertEqual(res, expected)
        mo = efj.Parser._Parser__RE_DUTY.fullmatch("1000/1100 r")
        res = efj.Parser._Parser__parse_duty(parser, mo)
        expected = expected._replace(ftl_correction=60)
        self.assertEqual(res, expected)
        mo = efj.Parser._Parser__RE_DUTY.fullmatch(
            "1000/1100 r t1 t2:10 # comment")
        res = efj.Parser._Parser__parse_duty(parser, mo)
        expected = expected._replace(
            extra_flags=("t1", "t2:10"), comment="comment")
        self.assertEqual(res, expected)
        mo = efj.Parser._Parser__RE_DUTY.fullmatch("1000/1100#comment")
        res = efj.Parser._Parser__parse_duty(parser, mo)
        expected = efj.Duty(
            dt.datetime(2024, 12, 31, 10, 0), 60, 0, (), "comment")
        self.assertEqual(res, expected)
        if __debug__:
            with self.assertRaises(AssertionError):
                efj.Parser._Parser__parse_duty(parser, None)

    def test_aircraft(self):
        parser = efj.Parser()
        mo = efj.Parser._Parser__RE_AIRCRAFT.fullmatch("G-ABCD:A320:mc")
        res = efj.Parser._Parser__parse_aircraft(parser, mo)
        exp = efj.Aircraft("G-ABCD", "A320", "mc")
        self.assertEqual(res, exp)
        mo = efj.Parser._Parser__RE_AIRCRAFT.fullmatch("GA-BC-DE : A-320-neo")
        res = efj.Parser._Parser__parse_aircraft(parser, mo)
        exp = efj.Aircraft("GA-BC-DE", "A-320-neo", "")
        self.assertEqual(res, exp)

    def test_crewlist(self):
        parser = efj.Parser()
        c = efj.Parser._Parser__RE_CREWLIST.fullmatch
        f = efj.Parser._Parser__parse_crewlist
        res = f(parser, c("{ cp: pugwash, fo: bloggs}"))
        exp = [
            efj.Crewmember("cp", "pugwash"),
            efj.Crewmember("fo", "bloggs")
        ]
        self.assertEqual(res, exp)
        res = efj.Parser._Parser__parse_crewlist(parser, c("{}"))
        self.assertEqual(res, [])
        with self.assertRaises(efj._VE) as e:
            f(parser, c("{ cp: fo: bloggs }"))
        self.assertEqual(e.exception.code, efj._VE.Code.BAD_CREWLIST)
        with self.assertRaises(efj._VE) as e:
            f(parser, c("{ cp fo: bloggs }"))
        self.assertEqual(e.exception.code, efj._VE.Code.BAD_CREWLIST)
        with self.assertRaises(efj._VE) as e:
            f(parser, c("{{sdkfjl cp: :fo}"))
        self.assertEqual(e.exception.code, efj._VE.Code.BAD_CREWLIST)

    def test_sector(self):
        parser = efj.Parser()
        default_sector = efj.Sector(
            start=dt.datetime(2025, 1, 1, 10),
            total=60,
            roles=efj.Roles(p1=60),
            conditions=efj.Conditions(ifr=60),
            landings=efj.Landings(1, 0),
            aircraft=efj.Aircraft("G-ABCD", "A320", ""),
            airports=efj.Airports("BRS", "FNC"),
            captain="Self",
            extra_flags=(),
            comment="",
            crew=())
        r = efj.Parser._Parser__RE_SECTOR.fullmatch
        f = efj.Parser._Parser__parse_sector
        # parse errors
        parser.date = dt.date(2025, 1, 1)
        with self.assertRaises(efj._VE) as e:
            f(parser, r("BRS/FNC 1000/1100"))
        self.assertEqual(e.exception.code, efj._VE.Code.MISSING_AIRCRAFT)
        parser.date = None
        parser.aircraft = efj.Aircraft("G-ABCD", "A320", "")
        with self.assertRaises(efj._VE) as e:
            f(parser, r("BRS/FNC 1000/1100"))
        self.assertEqual(e.exception.code, efj._VE.Code.MISSING_DATE)
        parser.date = dt.date(2025, 1, 1)
        parser.airports = efj.Airports("", "FNC")
        with self.assertRaises(efj._VE) as e:
            f(parser, r("/ 1000/1100"))
        self.assertEqual(e.exception.code, efj._VE.Code.MISSING_DEST)
        parser.airports = efj.Airports("BRS", "")
        with self.assertRaises(efj._VE) as e:
            f(parser, r("/ 1000/1100"))
        self.assertEqual(e.exception.code, efj._VE.Code.MISSING_ORIGIN)
        with self.assertRaises(efj._VE) as e:
            f(parser, r("BRS/FNC 1000/1100 n:a"))
        self.assertEqual(e.exception.code, efj._VE.Code.BAD_FLAGS)
        with self.assertRaises(efj._VE) as e:
            f(parser, r("BRS/FNC 1000/1100 p1s"))
        self.assertEqual(e.exception.code, efj._VE.Code.MISSING_CAPTAIN)
        # successful parse
        self.assertEqual(f(parser, r("BRS/FNC 1000/1100")), default_sector)
        self.assertEqual(
            f(parser, r("/BHX 1000/1100")),
            default_sector._replace(airports=efj.Airports("FNC", "BHX")))
        self.assertEqual(
            f(parser, r("/ 1000/1100")),
            default_sector._replace(airports=efj.Airports("BHX", "FNC")))
        self.assertEqual(f(parser, r("BRS/FNC 1000/1100#test comment")),
                         default_sector._replace(comment="test comment"))
        parser.crewlist = [efj.Crewmember(role="cp", name="bloggs"),]
        self.assertEqual(f(parser, r("BRS/FNC 1000/1100 p1s v n")),
                         default_sector._replace(
                             roles=efj.Roles(p1=0, p1s=60),
                             landings=efj.Landings(day=0, night=1),
                             captain="bloggs",
                             crew=(efj.Crewmember("cp", "bloggs"),),
                             conditions=efj.Conditions(night=60)))
