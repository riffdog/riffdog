Version History
===============

*Please note this is most recent at top.*


``0.1.0`` Beta
==============

*Released 2nd March 2020*

To install this, please follow the guide - you will need at least one 'resource pack', and at the time of writing only the riffdog_aws resource pack exists.

``pip install riffdog[aws]``

Then to run:

``riffdog -b bucket_name_containing_states --show-matched``

Major changes:

* The return data structure is radically different to before, which makes resource pack developers life easier.
* Streamlined tabulated data outputs.
* Introduced 'dirty' flag to indicate where resources exist, but do not match in some form of sub-data element.

``0.0.1`` Beta Launch 
=====================

*Released 14th Feb 2020*

This is gearing up for a soft beta launch with friendly testers:

* Major changes to repository structure allowing future custom modules,
* Alias ability inside of register
* The AWS resources split into ``riffdog_aws`` repository,
* Introduction of ``depends_on`` and refactor of the ``Resource`` framework.

``0.0.0a3`` 3rd Alpha Nightly Build 
===================================

*Released 13th Feb 2020*

Large change to the base loaders, interface of modules, and addition of several key scanners.

* Dynamic module loading, decorator based register
* AWS S3 bucket inspector 
* AWS DB inspector
* Automated tests - Bandit & Lint via github actions
* ``--exclude-resource`` option for faster scanning
* Legalish - code of conduct & readme updates

``0.0.0.a2`` 2nd Alpha Nightly Build
====================================

*Released 12th Feb 2020*

Update to framework including prototype Result framework & output formatting and config fixes.

* ``--json`` format included, move to ``ReportElement``
* ``--region`` setting to allow control over AWS Region being scanned
* Tabular output
* Resolution of edge cases of 'nothing found' etc.

``0.0.0.a1`` 1st Alpha Nightly Build
====================================

*Released 11th Feb 2020*

Alpha releases to get basic framework availible and running for some use cases (i.e. AWS EC2 instances)

* State Scanner framework
* Basic output
