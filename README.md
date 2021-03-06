# riffdog
Riffdog Terraform / Reality scanner - finding 'things' in the Real World which 
Terraform didn't put there.

This project works by firstly loading your terraform state files - *not* your
terraform files, and building a memory object that represents what terraform 
*thinks* it has deployed. The second step is then to access your environment
and actually look what *is* there, and it builds another memory object.

Then it compares the two, and looks for:

* Things that TF put there, but arn't there
* Things that are there, that TF doesn't know about

For this to work, you *must* install a resouce pack, for instance `riffdog_aws`

## Command line vs Library

Riffdog is both a command line tool and a python library. The command line tool
basically creates a config object and calls the scan method.

To install (for example with the AWS resources)

`$ pip install riffdog[aws]`

To run:

`$ riffdog -b bucketname_containing_states` 

For full command line reference, please see the docs #FIXME - link to docs!

## Light vs Full Scan mode

AWS and Terraform are very complex: for instance, a EC2 instance is a computer,
a collection of network cards, volumes, etc. In 'light' mode, we do a high level
scan to see if all the main components are there - in 'full' mode, it inspects
all elements (as far as RiffDog is aware of, see below) - i.e. checks that all
network cards, volumes, etc are mounted as intended.

## Ignores

Its important to realise that not all infrastructure is deployed via TF - for
instance auto scaling, or service discovery systems may be interacting with your
infrastructure, and this is OK, but you don't want RiffDog raising alerts on
those.

## Caveats:

This is pretty much *always* a work under development, as AWS adds more features
modules etc. The system is designed to be modular, but we're only able to keep
up with modules that we use - so if you use a feature of AWS that we don't scan
please feel free to add a module. If you need help, please contact us or file 
a ticket.



## Testing

Automated testing of this system is quite difficult. Ultimatly these are here to make sure that changes to internal data structures do not break other functions (e.g. some data objects such as network interfaces are used by multiple features: both EC2 instances and Lambdas). The real test is whether it works against the current Terraform and AWS API's, not a snapshot from previous years.

* Tests go into the tests folder, 
* Tox is used to make sure compatibility with various versions of python & libraries
