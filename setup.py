# coding=utf-8

from setuptools import setup, find_packages


def read_requirements(file):
    with open(file) as f:
        return f.read().splitlines()

def read_file(file):
   with open(file) as f:
        return f.read()

requirements = read_requirements("requirements.txt")
version = read_file("VERSION")

setup(
    name="rdee",
    version=version,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    description="Roadelse's personal python library",
    url="https://github.com/Roadelse/rdee-python",
    author="Roadelse",
    author_email="roadelse@qq.com",
    license="GPL-3.0 license",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)