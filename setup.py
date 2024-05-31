import runpy
from os.path import dirname, join
from pathlib import Path
from setuptools import setup, find_packages


meta_path = Path(__file__).parent.absolute().joinpath("logview", "meta_data.py")
meta = runpy.run_path(str(meta_path))


def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()


setup(
    name=meta['__name__'],
    version=meta['__version__'],
    description=meta['__doc__'].strip(),
    long_description=read_file('README.md'),
    author=meta['__author__'],
    author_email=meta['__author_email__'],
    py_modules=['logview'],
    include_package_data=True,
    packages=[x for x in find_packages() if x.startswith("logview")],
    url='toBeDefined',
    license='GPL 3.0',
    install_requires=read_file("requirements.txt").split("\n"),
    project_urls={
        'Documentation': 'toBeDefined',
        'Source': 'toBeDefined',
        'Tracker': 'toBeDefined',
    }
)
