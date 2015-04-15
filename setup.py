#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-subscription',
    version="0.4",
    author='Steve Yeago',
    author_email='yeago999@gmail.com',
    description='Managing subscriptions in Django',
    url='http://github.com/yeago/django-subscription',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development"
    ],
)
