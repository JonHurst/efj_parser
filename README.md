# eFJ Parser #

An electronic Flight Journal (eFJ) is a simple text file within which pilot
flight records are recorded in an inuitive, non-tabular way. As an example, a
couple of days flying for a Captain might look like this:

      2024-02-04
      G-EZBY:A319
      BRS/GLA 0702/0818 n:18 m
      GLA/BHX 0848/1037  # Diversion due weather
      BHX/BRS 1300/1341

      2024-02-05
      G-UZHI:A320
      BRS/FNC 0708/1045 n:6
      FNC/BRS 1127/1451 m

Full details of the format may be found at
<https://hursts.org.uk/efjdocs/format.html>.

This is a Python parser library for text files with this format. It converts an
eFJ into a list of [Sector
objects](https://hursts.org.uk/efjdocs/data_structures.html#sectors) and a list
of [Duty Objects](https://hursts.org.uk/efjdocs/data_structures.html#duties).
The web application at <https://hursts.org.uk/efj/> makes use of this library
to create FCL.050 compliant HTML logbooks and summaries from an eFJ.
