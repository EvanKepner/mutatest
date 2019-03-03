import codecs
import os
import re
import sys

from setuptools import find_packages, setup

if (sys.version_info.major, sys.version_info.minor) != (3, 7):
    raise EnvironmentError("Mutatest requires Python version 3.7.")

###############################################################################
# Using setup.py from Attrs as a template for finding components, awesome config.
# Original reference: https://github.com/python-attrs/attrs/blob/master/setup.py

NAME = "mutatest"
PACKAGES = find_packages()
META_PATH = os.path.join("mutatest", "__init__.py")
KEYWORDS = ["mutatest", "mutation", "testing", "test", "mutant", "mutate", "pytest"]
PROJECT_URLS = {
    "Documentation": "https://github.com/EvanKepner/mutatest",
    "Bug Tracker": "https://github.com/EvanKepner/mutatest/issues",
    "Source Code": "https://github.com/EvanKepner/mutatest",
}

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "Environment :: Console",
    "Framework :: Pytest",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Testing",
    "Topic :: Software Development :: Testing :: Unit",
]

INSTALL_REQUIRES = ["pytest", "coverage>=4.4"]
EXTRAS_REQUIRE = {
    "docs": ["sphinx"],
    "tests": [
        "pytest >= 4.0.0",
        "freezegun",
        "coverage",
        "pytest-cov",
        "pytest-xdist",
        "tox",
        "virtualenv",
        "hypothesis",
    ],
    "qa": ["mypy", "black", "pre-commit", "isort"],
}

EXTRAS_REQUIRE["dev"] = EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["docs"] + EXTRAS_REQUIRE["qa"]


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
    meta_match = re.search(r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta), META_FILE, re.M)
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


VERSION = find_meta("version")
URL = find_meta("url")
LONG = "\n\n".join([read("README.rst"), read("CHANGELOG.rst"), read("AUTHORS.rst")])


if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=URL,
        project_urls=PROJECT_URLS,
        version=VERSION,
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        keywords=KEYWORDS,
        long_description=LONG,
        packages=PACKAGES,
        python_requires=">=3.7.0",
        zip_safe=False,
        entry_points={"console_scripts": ["mutatest=mutatest.cli:cli_main"]},
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        include_package_data=True,
    )
