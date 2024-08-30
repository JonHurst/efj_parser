import unittest
import datetime as dt

import efj_parser as efj


class TestParser(unittest.TestCase):

    def test_basic(self):
        data = """\
2024-01-21
1000/1430
N1:320
{FO: Bloggs}
BRS/BFS 1100/1200 ins #belfast
/ 1300/1400 ins:20 test spme
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
                efj.Aircraft("N1", "320"),
                efj.Airports("BRS", "BFS"),
                "Self", (), "belfast",
                (efj.Crewmember("FO", "Bloggs"),)),
            efj.Sector(
                dt.datetime(2024, 1, 21, 13), 60,
                efj.Roles(p1=60, instructor=20),
                efj.Conditions(ifr=60),
                efj.Landings(day=1),
                efj.Aircraft("N1", "320", "spme"),
                efj.Airports("BFS", "BRS"),
                "Self", ("test",), "",
                (efj.Crewmember("FO", "Bloggs"),)),
            efj.Sector(
                dt.datetime(2024, 1, 22, 11), 120,
                efj.Roles(p1=120),
                efj.Conditions(ifr=120),
                efj.Landings(day=3),
                efj.Aircraft("OB-T-1274", "A-321"),
                efj.Airports("BRS", "NCE"),
                "Self", (), "", ()),
            efj.Sector(
                dt.datetime(2024, 1, 22, 13, 40), 120,
                efj.Roles(p1=120),
                efj.Conditions(night=10, ifr=90),
                efj.Landings(night=1),
                efj.Aircraft("OB-T-1274", "A-321"),
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
                efj.Aircraft("G-ABCD", "320"),
                efj.Airports("BRS", "BFS"),
                "Bloggs Joe", (), "belfast",
                (efj.Crewmember("CP", "Bloggs Joe"),)),
            efj.Sector(
                dt.datetime(2024, 1, 21, 13), 60,
                efj.Roles(p2=60),
                efj.Conditions(ifr=60),
                efj.Landings(),
                efj.Aircraft("G-ABCD", "320"),
                efj.Airports("BFS", "BRS"),
                "Bloggs Joe", (), "",
                (efj.Crewmember("CP", "Bloggs Joe"),)),
            efj.Sector(
                dt.datetime(2024, 1, 24, 11), 120,
                efj.Roles(p2=120),
                efj.Conditions(ifr=120),
                efj.Landings(),
                efj.Aircraft("G-EFGH", "321"),
                efj.Airports("BRS", "NCE"),
                "Pugwash", (), "", (
                    efj.Crewmember("CP", "Pugwash"),
                    efj.Crewmember("PU", "Purser"),)),
            efj.Sector(
                dt.datetime(2024, 1, 24, 13, 40), 120,
                efj.Roles(p1=90, p1s=30),
                efj.Conditions(ifr=120),
                efj.Landings(day=1),
                efj.Aircraft("G-EFGH", "321"),
                efj.Airports("NCE", "BRS"),
                "Self, Pugwash", (), "", (
                    efj.Crewmember("CP", "Pugwash"),
                    efj.Crewmember("PU", "Purser"),)),
        )
        self.assertEqual(
            efj.Parser().parse(data),
            (expected_duties, expected_sectors))

    def test_flags(self):
        aircraft = efj.Aircraft("G-ABCD", "320")
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
                "Line 1: [Incorrect crew listing format] {just a string}")
        with self.subTest("No name"):
            data = "2024-01-22\n{CP:, FO:Bloggs}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 2: [Incorrect crew listing format] {CP:, FO:Bloggs}")
        with self.subTest("No comma"):
            data = "{ CP: Bloggs1 FO:Bloggs2}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Incorrect crew listing format]"
                " { CP: Bloggs1 FO:Bloggs2}")
        with self.subTest("No colon"):
            data = "{just a, string}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Incorrect crew listing format] {just a, string}")
        with self.subTest("Multi word role"):
            data = "{just a: string}"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Incorrect crew listing format] {just a: string}")

    def test_bad_date(self):
        data = "2024-02-30"
        with self.assertRaises(efj.ValidationError) as e:
            efj.Parser().parse(data)
        self.assertEqual(
            str(e.exception),
            "Line 1: [Incorrect Date entry] 2024-02-30")

    def test_bad_nextdate(self):
        data = "2024-02-01\n++-"
        with self.assertRaises(efj.ValidationError) as e:
            efj.Parser().parse(data)
        self.assertEqual(
            str(e.exception),
            "Line 2: [Bad syntax] ++-")

    def test_bad_duty(self):
        with self.subTest("No preceding date"):
            data = "1000/1100"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 1: [Duty entry without preceding Date entry] 1000/1100")
        with self.subTest("Bad time format"):
            data = "2024-02-01\n2200/2400"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 2: [Invalid time string] 2200/2400")
        with self.subTest("Hyphen instead of slash"):
            data = "2024-02-01\n2200-2400"
            with self.assertRaises(efj.ValidationError) as e:
                efj.Parser().parse(data)
            self.assertEqual(
                str(e.exception),
                "Line 2: [Bad syntax] 2200-2400")


class TestSectorFlags (unittest.TestCase):

    def test_landings(self):
        with self.subTest("No flags, day"):
            self.assertEqual(
                efj._process_landings((), 1, 0),
                (efj.Landings(day=1, night=0), ()))
        with self.subTest("PM, day"):
            self.assertEqual(
                efj._process_landings(("m",), 1, 0),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("No flags, night"):
            self.assertEqual(
                efj._process_landings((), 1, 1),
                (efj.Landings(day=0, night=1), ()))
        with self.subTest("PM, night"):
            self.assertEqual(
                efj._process_landings(("m",), 1, 1),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("Partial night, day landing"):
            self.assertEqual(
                efj._process_landings((), 2, 1),
                (efj.Landings(day=1, night=0), ()))
        with self.subTest("Partial night, night landing"):
            self.assertEqual(
                efj._process_landings(("ln",), 2, 1),
                (efj.Landings(day=0, night=1), ()))
        with self.subTest("Multiple day landings"):
            self.assertEqual(
                efj._process_landings(("ld:2",), 2, 0),
                (efj.Landings(day=2, night=0), ()))
        with self.subTest("Multiple night landings"):
            self.assertEqual(
                efj._process_landings(("ln:2",), 2, 1),
                (efj.Landings(day=0, night=2), ()))
        with self.subTest("Mix of landings, single"):
            self.assertEqual(
                efj._process_landings(("ln", "ld"), 2, 1),
                (efj.Landings(day=1, night=1), ()))
        with self.subTest("Mix of landings, multi"):
            self.assertEqual(
                efj._process_landings(("ln:2", "ld"), 2, 1),
                (efj.Landings(day=1, night=2), ()))
        with self.subTest("Zero landings, day flag"):
            self.assertEqual(
                efj._process_landings(("ld:0",), 2, 1),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("Zero landings, night flag"):
            self.assertEqual(
                efj._process_landings(("ln:0",), 2, 1),
                (efj.Landings(day=0, night=0), ()))
        with self.subTest("Day landing, night flight"):
            # Assume that user did this for a reason
            self.assertEqual(
                efj._process_landings(("ld",), 2, 2),
                (efj.Landings(day=1, night=0), ()))
        with self.subTest("Bad quantity"):
            self.assertEqual(
                efj._process_landings(("ln:xyz",), 1, 0),
                (efj.Landings(1, 0), ("ln:xyz",)))

    def test_roles(self):
        with self.subTest("All p1"):
            self.assertEqual(
                efj._process_roles((), 1),
                (efj.Roles(p1=1), ()))
        with self.subTest("All p1s"):
            self.assertEqual(
                efj._process_roles(("p1s",), 1),
                (efj.Roles(p1s=1), ()))
        with self.subTest("All p2"):
            self.assertEqual(
                efj._process_roles(("p2",), 1),
                (efj.Roles(p2=1), ()))
        with self.subTest("All put"):
            self.assertEqual(
                efj._process_roles(("put",), 1),
                (efj.Roles(put=1), ()))
        with self.subTest("Split roles, put & p1"):
            self.assertEqual(
                efj._process_roles(("put:1",), 2),
                (efj.Roles(p1=1, put=1), ()))
        with self.subTest("Split roles, p1s & p1"):
            self.assertEqual(
                efj._process_roles(("p1s:1",), 2),
                (efj.Roles(p1=1, p1s=1), ()))
        with self.subTest("Split roles, p2 & p1"):
            self.assertEqual(
                efj._process_roles(("p2:1",), 2),
                (efj.Roles(p1=1, p2=1), ()))
        with self.subTest("Split roles, p1s & put"):
            self.assertEqual(
                efj._process_roles(("p1s:1", "put:1"), 2),
                (efj.Roles(p1s=1, put=1), ()))
        with self.subTest("Role duration > duration"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_roles(("p1s:2",), 1)
                self.assertEqual(ve.exception.message, "Too many roles")
        with self.subTest("Two untimed roles"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_roles(("p1s", "put"), 1)
            self.assertEqual(ve.exception.message, "Too many roles")
        with self.subTest("Instructor flag"):
            self.assertEqual(
                efj._process_roles(("ins",), 1),
                (efj.Roles(p1=1, instructor=1), ()))
        with self.subTest("Instructor flag, partial"):
            self.assertEqual(
                efj._process_roles(("ins:1",), 2),
                (efj.Roles(p1=2, instructor=1), ()))
        with self.subTest("Unknown role"):
            self.assertEqual(
                efj._process_roles(("p3",), 2),
                (efj.Roles(p1=2), ("p3",)))
        with self.subTest("Bad duration"):
            self.assertEqual(
                efj._process_roles(("p1s:xyz",), 1),
                (efj.Roles(p1=1), ("p1s:xyz",)))

    def test_conditions(self):
        with self.subTest("No flags"):
            self.assertEqual(
                efj._process_conditions((), 1),
                (efj.Conditions(ifr=1, night=0), ()))
        with self.subTest("VFR flag"):
            self.assertEqual(
                efj._process_conditions(("v",), 1),
                (efj.Conditions(ifr=0, night=0), ()))
        with self.subTest("Night flag"):
            self.assertEqual(
                efj._process_conditions(("n",), 1),
                (efj.Conditions(ifr=1, night=1), ()))
        with self.subTest("VFR at night"):
            self.assertEqual(
                efj._process_conditions(("n", "v"), 1),
                (efj.Conditions(ifr=0, night=1), ()))
        with self.subTest("Part VFR"):
            self.assertEqual(
                efj._process_conditions(("v:1",), 2),
                (efj.Conditions(ifr=1, night=0), ()))
        with self.subTest("Part Night"):
            self.assertEqual(
                efj._process_conditions(("n:1",), 2),
                (efj.Conditions(ifr=2, night=1), ()))
        with self.subTest("Bad duration"):
            self.assertEqual(
                efj._process_conditions(("v:xyz",), 2),
                (efj.Conditions(ifr=2, night=0), ("v:xyz",)))
        with self.subTest("VFR duration > duration"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_conditions(("v:2",), 1),
            self.assertEqual(ve.exception.message,
                             "VFR duration more than flight duration")
        with self.subTest("Night duration > duration"):
            with self.assertRaises(efj._VE) as ve:
                efj._process_conditions(("n:2",), 1),
            self.assertEqual(ve.exception.message,
                             "Night duration more than flight duration")

    def test_class_override(self):
        with self.subTest("SPSE"):
            self.assertEqual(
                efj._process_class_override(("spse",)),
                ("spse", ()))
        with self.subTest("SPME"):
            self.assertEqual(
                efj._process_class_override(("spme",)),
                ("spme", ()))
        with self.subTest("MC"):
            self.assertEqual(
                efj._process_class_override(("mc",)),
                ("mc", ()))
        with self.subTest("SPSE"):
            self.assertEqual(
                efj._process_class_override(("test",)),
                ("", ("test",)))
        with self.subTest("Multiple overrides"):
            self.assertEqual(
                efj._process_class_override(("spse", "spme", "mc")),
                ("mc", ()))
