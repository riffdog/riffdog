Command line
============


The command line tool allows for most options to be set: however as your usage
and the number of imports you use gets larger, your command might get manageably
long, so for this reason we support a config file option as well.

   We don't yet support a config file option

This section has been split into 4: General options, Processing modifiers, and Output modifiers, resouce pack specific options

General options
===============

* ``-h`` or ``--help`` prints out the help

Processing modifiers
====================

* ``-b`` or ``--bucket`` specifies which AWS S3 bucket your state files exist in. You should pass in a bucket name, e.g. ``-b mybucket`` (not an ARN). This can be specified more the one time for a collection of buckets, e.g. ``-b mybucket -b myotherbucket``. This can also be used to specify specific files inside the bucket, i.e. ``-b mybucket/mystatefile.tfstate`` (which can be handy when debugging). Note ignoring or skipping state filles will cause false 'found in real but not tf' outputs'.
* ``--include-resource`` allows specific resources to be used - this automatically excludes all other resources not listed. This can be used multiple times, e.g. ``--include-resource aws-instance --include-resource aws_lambda_function``
* ``--exclude-resource`` This can be used to exclude a specific resource - perhaps you don't terraform security group rules, but do security groups, this allows you to specify one resource (named by terraform naming) from being reported on. This not only reduces output but can speed up the run time as it does not scan that resource.
* ``-i`` or ``--include`` include a extra non-core resource pack. By default, RiffDog will scan and find installed 'core' packages (e.g. AWS, Cloudflare etc).

Output modifiers:
=================

* ``--json`` Produce output as a Json object. This can then be parsed by other programs and systems
* ``--show-matched`` Shows all resources, including those that matched - by default we only print the unmatched on both sides. (does not affect JSON output)

Resource Pack specific options
==============================

The resource packs contain the processers and scanners for specific items, e.g. the riffdog_aws pack contains the resource files and scanners for AWS. Some of these have their own configuration. For more info, please see the specific options


