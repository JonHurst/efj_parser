import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="efj_parser",
    version="0.9",
    author="Jon Hurst",
    author_email="jon.a@hursts.org.uk",
    description="Parse an Electronic Flight Journal file",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JonHurst/efj_parser",
    py_modules=['efj_parser'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: "
        "GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)