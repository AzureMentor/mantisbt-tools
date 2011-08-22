#!/usr/bin/env python

import os, sys
from os import path

import getopt
import re
import shutil
import tempfile

# Absolute path to buildrelease.py
buildscript = path.dirname(path.abspath(__file__)) + '/buildrelease.py'

# Regular expressions of refs to ignore
ignorelist = map(re.compile, [
			'HEAD',
			'-1\.0\.[\w\d]+',
			])

# Script options
options = "hfr:bacds:"
long_options = [ "help", "fresh", "ref=", "branches", "auto-suffix", "clean", "docbook", "suffix=" ]

def usage():
	print '''Usage: buildrelease-repo [options] /path/for/tarballs [/path/to/repo]
Options:  -h | --help                  Show this usage message

          -f | --fresh                 Create a fresh clone at repository path, or temporary path
          -r | --ref <ref>[,<ref>...]  Build a release for named refs <ref>
          -b | --branches              Build a release for all branches
          -a | --auto-suffix           Automatically append the Git hash to the version suffix

          -c | --clean                 Remove build directories when completed
          -d | --docbook               Build the docbook manuals
          -s | --suffix <suffix>       Include version suffix in config files'''
#end usage()

def ignore( ref ):
	'''Decide which refs to ignore based on regexen listed in 'ignorelist'.
	'''

	ignore = False
	for regex in ignorelist:
		if len(regex.findall(ref)) > 0:
			ignore = True
	return ignore
#end ignore()

def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], options, long_options)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)

	pass_opts = ""
	refs = []
	all_branches = False
	version_suffix = ""
	auto_suffix = False
	fresh_clone = False
	delete_clone = False

	for opt, val in opts:
		if opt in ("-h", "--help"):
			usage()
			sys.exit(0)

		elif opt in ("-f", "--fresh"):
			fresh_clone = True

		elif opt in ("-r", "--ref"):
			refs.extend(val.split(","))

		elif opt in ("-b", "--branches"):
			all_branches = True

		elif opt in ("-c", "--clean"):
			pass_opts += " -c"

		elif opt in ("-d", "--docbook"):
			pass_opts += " -d"

		elif opt in ("-a", "--auto-suffix"):
			auto_suffix = True

		elif opt in ("-s", "--suffix"):
			version_suffix = val

	if len(args) < 1:
		usage()
		sys.exit(1)

	release_path = args[0]
	repo_path = "."

	if len(args) > 1:
		repo_path = args[1]

	# Create a new repo clone
	if fresh_clone:
		if repo_path == ".":
			repo_path = tempfile.mkdtemp(prefix="mantisbt-", suffix=".git")
			delete_clone = True
		os.system('git clone git://github.com/mantisbt/mantisbt.git %s' % (repo_path))

	# Change to the repo path
	os.chdir(repo_path)

	# Update the repository
	os.system('git fetch')

	# Consolidate refs/branches
	if all_branches:
		os.system('git remote prune origin')
		refs.extend(os.popen('git branch -r').read().split())

	if len(refs) < 1:
		refs.extend(os.popen('git log --pretty="format:%h" -n1').read())

	refs = [ref for ref in refs if not ignore(ref)]

	# Info
	print "Will build the following releases:"
	for ref in refs:
		print "  %s"%ref
	print "\n"

	# Regex to strip 'origin/' from ref names
	refnameregex = re.compile('(?:[a-zA-Z0-9-.]+/)?(.*)')
	
	for ref in refs:
		os.system("git checkout -f %s"%(ref))

		# Handle suffix/auto-suffix generation
		hash = os.popen('git log --pretty="format:%h" -n1').read()
		if hash != ref:
			ref = refnameregex.search( ref ).group(1)
			hash = "%s-%s"%(ref,hash)

		suffix = ""
		if auto_suffix and version_suffix:
			suffix = "--suffix %s-%s"%(version_suffix, hash)
		elif auto_suffix:
			suffix = "--suffix %s"%hash
		elif version_suffix:
			suffix = "--suffix %s"%version_suffix

		# Start building
		os.system("%s %s %s %s %s"%(buildscript, pass_opts, suffix, release_path, repo_path))

	# Cleanup temporary repo if needed
	if delete_clone:
		print "\nRemoving temporary clone."
		shutil.rmtree(repo_path)

	# Done
	print "\nAll builds completed."

#end main()

if __name__ == "__main__":
	main()