import codecs
import os
import re
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 6, 0):
    raise Exception("Mutation requires Python version 3.6 or later")

###############################################################################
# Using setup.py from Attrs as a template for finding components
# Original reference: https://github.com/python-attrs/attrs/blob/master/setup.py

NAME = "mutation"
PACKAGES = find_packages(where="mutaton")
META_PATH = os.path.join("mutation",  "__init__.py")
KEYWORDS = ["mutation", "testing", "test", "mutant", "mutate"]
PROJECT_URLS = {
    "Documentation": "https://github.com/EvanKepner/m",
    "Bug Tracker": "https://github.com/EvanKepner/m/issues",
    "Source Code": "https://github.com/EvanKepner/m",
}

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "Environment :: Console",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Mutation Testing",
]

INSTALL_REQUIRES = []
EXTRAS_REQUIRE = {
    "docs": ["sphinx",],
    "tests": [
        "coverage",
        "pytest",
        "pytest-cov",
    ],
    "other": ["mypy", "black"]
}

EXTRAS_REQUIRE["dev"] = (
    EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["docs"] + EXTRAS_REQUIRE["other"]
)


HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


VERSION = find_meta("version")
URL = find_meta("url")
LONG = (
    read("README.md")
    + "\n\n"
    + read("AUTHORS.md")
)


if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=URL,
        #project_urls=PROJECT_URLS,
        version=VERSION,
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
        keywords=KEYWORDS,
        long_description=LONG,
        packages=PACKAGES,
        package_dir={"": "mutation"},
        python_requires=">=3.6.0",
        zip_safe=False,
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        include_package_data=True,
    )