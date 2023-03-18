#!/usr/bin/env python
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="smount", # Replace with your own username
    version="0.0.1",
    author="Thomas Langé",
    author_email="thomas.lange.oss@gmail.com",
    description="smount - a mounting manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lqp1/smount",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL3 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'pyyml',
    ],
    tests_require=[
        'pyfakefs',
    ],
    scripts=['bin/smount'],
)
