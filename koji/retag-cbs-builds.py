#! /usr/bin/python

import koji
from operator import itemgetter
import os.path
import sys

KOJI_URL='http://cbs.centos.org/kojihub'
ORIG_TAG='cloud6-testing'
ORIG_TAG2='cloud6-release'
CATEGORIES={'common': 'cloud6-openstack-common-candidate',
            'juno': 'cloud6-openstack-juno-candidate'}
CLIENT_CERT = os.path.expanduser('~/.koji/client.crt')
CLIENTCA_CERT = os.path.expanduser('~/.koji/clientca.crt')
SERVERCA_CERT = os.path.expanduser('~/.koji/serverca.crt')
USER = 'hguemar'


kojiclient = koji.ClientSession(KOJI_URL)
kojiclient.ssl_login(CLIENT_CERT, CLIENTCA_CERT, SERVERCA_CERT)


def get_tag_id(tagName):
    tags = [x['id'] for x in kojiclient.listTags() if x['name'] == tagName]
    return tags[0] if len(tags) else None


def retrieve_packages(tagName):
    tagID = get_tag_id(tagName)
    packages = kojiclient.listPackages(tagID=tagID)
    return packages


def categorize_package(package):
    name = package['package_name']
    category = None
    if name.startswith('openstack') or \
       name.startswith('python-oslo') or \
       'django' in name or \
       'XStatic' in name or \
       name.startswith('diskimage') or \
       name.startswith('dib') or \
       name.startswith('instack') or \
       name.startswith('os-') or \
       name.startswith('mariadb-galera') or \
       name.startswith('heat') or \
       name == 'python-tooz' or \
       name == 'python-stevedore' or \
       name == 'python-taskflow' or \
       'keystone' in name or \
       'glance' in name or \
       name.endswith('client'):
        category ='juno'
    else:
        category = 'common'
    package['category'] = category
    return package


def print_pkgs_list(packages):
    common = []
    juno = []
    for i in packages:
        package = categorize_package(i)
        if package['category'] == 'common':
            common.append(package)
        else:
            juno.append(package)
    print "=== {} ===".format(CATEGORIES['common'])
    for i in sorted(common, key=itemgetter('package_name')):
        print i['package_name']
    print "\n\n"
    print "=== {} ===".format(CATEGORIES['juno'])
    for i in sorted(juno, key=itemgetter('package_name')):
        print i['package_name']


def tag_build(buildID, tagID, fromtag=None):
    kojiclient.tagBuild(tagID, buildID, fromtag=fromtag)


def tag_packages(packages):
    userid = kojiclient.getUser(USER)['id']
    fromtag = get_tag_id(ORIG_TAG)
    fromtag2 = get_tag_id(ORIG_TAG2)
    for package in packages:
        package = categorize_package(package)
        name = package['package_name']
        category = package['category']
        pkgid = package['package_id']
        tagID = get_tag_id(CATEGORIES[category])
        builds = kojiclient.listTagged(tag=ORIG_TAG, package=name)
        kojiclient.packageListRemove(fromtag, pkgid)
        kojiclient.packageListRemove(fromtag2, pkgid)
        kojiclient.packageListAdd(tagID, pkgid, owner=userid)
        for build in builds:
            buildID = build['build_id']
            tag_build(buildID, tagID, fromtag)

def fixup(packages, orig_tag):
    userid = kojiclient.getUser(USER)['id']
    fromtag = get_tag_id(orig_tag)
    for package in packages:
        name = package['package_name']
        builds = kojiclient.listTagged(tag=orig_tag, package=name)
        if len(builds) == 0:
            print name


packages = retrieve_packages(ORIG_TAG)
print_pkgs_list(packages)
tag_packages(packages)

