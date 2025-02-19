import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="efj-parser",
    version="0.9.5",
    author="Jon Hurst",
    author_email="jon.a@hursts.org.uk",
    description="Parse an electronic Flight Journal file",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JonHurst/efj_parser",
    packages=['efj_parser'],
    package_data={"efj_parser": ["py.typed"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: "
        "GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    project_urls = {
        "docs" : "https://hursts.org.uk/efjdocs/",
        },
)
