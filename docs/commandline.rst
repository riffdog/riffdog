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

* ``-b`` or ``--bucket`` specifies which AWS S3 bucket your state files exist in. You should pass in a bucket name, e.g. ``-b mybucket`` (not an ARN). This can be specified more the one time for a collection of buckets, e.g. ``-b mybucket -b myotherbucket``
* ``--exclude-resource`` This can be used to exclude a specific resource - perhaps you don't terraform security group rules, but do security groups, this allows you to specify one resource (named by terraform naming) from being reported on. This not only reduces output but can speed up the run time as it does not scan that resource.
* ``-i`` or ``--include`` include a extra non-core resource pack. By default, RiffDog will scan and find installed 'core' packages (e.g. AWS, Cloudflare etc),

Output modifiers:
=================

* ``--json`` Produce output as a Json object. This can then be parsed by other programs and systems
* ``--show-matched`` Shows all resources, including those that matched - by default we only print the unmatched on both sides. (does not affect JSON output)

Resource Pack specific options
==============================

The resource packs contain the processers and scanners for specific items, e.g. the riffdog_aws pack contains the resource files and scanners for AWS. Some of these have their own configuration. For more info, please see the specific options

   FIXME: at he moment the AWS config is in core.

* ``--region`` Specifies a region to use (default is ``us-east-1``) This can be called multiple times, e.g. ``--region us-east-1 --region us-east-2`` For region codes see AWS documentation.



