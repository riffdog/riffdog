# Contributions

Thank you for your interest in contributing to RiffDog.

# Tickets & Security Issues

* Please use githubs ticketing on the riffdog page. https://github.com/jmons/riffdog/issues
* Try to check that there are not existing tickets that cover your query or problem
* Try to use the 'label' feature to label your ticket the most common will be:
  * `enhancement` tickets are for core framework enhancements
  * `resource_request` tickets are for adding resources (i.e. a particular thing that is terraformed)
  * `bug` are for reporting issues with components
  * `security` is for highlighting an issue which has some security concerns. (see below)

Please be aware that all contributors are volunteers, and are only able to test with their own particular setups and situations - because of the wide scope of Terraform, and its providors, its possible that there are edge cases which are not covered by the testing.

Because of the riffdog tool being an internal used tool, any security concerns are probably not as high demand as other tools (e.g. openssl etc), but if you feel publishing a public security note is inappropriate, please contact @jmons on twitter.

# Contributing Source

Source is in one of two areas:

* Core Framework modifications
* New Resources / Changes to Resources

Please be aware that this project is a MIT license - any code you donat to the project will be absorbed into that, so please make sure that it is your copyright you are donating. (similarly, if you need to use someone elses code, ideally we would import that as an import, but we want to make the library as tight on its dependancies as possible).

* Branch from `master` unless specifically needed.
* Always work on the feature/bug_fix branch and make a Pull Request (PR) to have your code accepted
* Branch names generally are `f_feature_name` for features or `bf_feature_name` for bugfixes. 
* Naming strategy for Resources is to match the Terraform resource name as closely as possible, so its easy to find the resources / modules.
* Maintainability of code is a strong desirability over other factors.

For details on how to build a new module, please see the wiki on https://github.com/jmons/riffdog/wiki 

# Releases

* Releases are done through pypi, and these are a subset of the git developers.
* The releases should be tagged as git-tags for finding for security patches if needed.
