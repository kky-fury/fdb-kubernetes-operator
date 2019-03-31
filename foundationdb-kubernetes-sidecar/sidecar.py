#! /usr/bin/python

# entrypoint.py
#
# This source file is part of the FoundationDB open source project
#
# Copyright 2013-2018 Apple Inc. and the FoundationDB project authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import hashlib
import os
import shutil
import socket
import stat
from pathlib import Path

import flask

app = flask.Flask(__name__)
app.config.from_json(os.getenv('SIDECAR_CONF_DIR') + '/config.json')

input_dir = os.getenv('INPUT_DIR', '/var/input-files')
output_dir = os.getenv('OUTPUT_DIR', '/var/output-files')

substitutions = {}
for key in ['FDB_PUBLIC_IP', 'FDB_MACHINE_ID', 'FDB_ZONE_ID']:
    substitutions[key] = os.getenv(key, '')

if substitutions['FDB_MACHINE_ID'] == '':
    substitutions['FDB_MACHINE_ID'] = os.getenv('HOSTNAME', '')

if substitutions['FDB_ZONE_ID'] == '':
    substitutions['FDB_ZONE_ID'] = substitutions['FDB_MACHINE_ID']
if substitutions['FDB_PUBLIC_IP'] == '':
    address_info = socket.getaddrinfo(substitutions['FDB_MACHINE_ID'], 4500, family=socket.AddressFamily.AF_INET)
    if len(address_info) > 0:
        substitutions['FDB_PUBLIC_IP'] = address_info[0][4][0]


@app.route('/check_hash/<path:filename>')
def check_hash(filename):
	try:
		with open('%s/%s' % (output_dir, filename), 'rb') as contents:
			m = hashlib.sha256()
			m.update(contents.read())
			return m.hexdigest()
	except FileNotFoundError:
		flask.abort(404)

@app.route('/copy_files', methods=['POST'])
def copy_files():
	for filename in app.config['COPY_FILES']:
		shutil.copy('%s/%s' % (input_dir, filename), '%s/%s' % (output_dir, filename))
	return "OK"

@app.route('/copy_binaries', methods=['POST'])
def copy_binaries():
	with open('/var/fdb/version') as version_file:
		primary_version = version_file.read().strip()
	for binary in app.config['COPY_BINARIES']:
		path = Path('/usr/bin/%s' % binary)
		target_path = Path('%s/bin/%s/%s' % (output_dir, primary_version, binary))
		if not target_path.exists():
			target_path.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy(path, target_path)
			target_path.chmod(0o744)
	return "OK"

@app.route('/copy_libraries', methods=['POST'])
def copy_libraries():
	for version in app.config['COPY_LIBRARIES']:
		path =  Path('/var/fdb/lib/libfdb_c_%s.so' % version)
		if version == app.config['COPY_LIBRARIES'][0]:
			target_path = Path('%s/lib/libfdb_c.so' % (output_dir))
		else:
			target_path = Path('%s/lib/multiversion/libfdb_c_%s.so' % (output_dir, version))
		if not target_path.exists():
			target_path.parent.mkdir(parents=True, exist_ok=True)
			shutil.copy(path, target_path)
	return "OK"

@app.route("/copy_monitor_conf", methods=['POST'])
def copy_monitor_conf():
    if 'INPUT_MONITOR_CONF' in app.config:
        with open('%s/%s' % (input_dir, app.config['INPUT_MONITOR_CONF'])) as monitor_conf_file:
            monitor_conf = monitor_conf_file.read()
        for variable in substitutions:
            monitor_conf = monitor_conf.replace('$' + variable, substitutions[variable])
        with open('%s/fdbmonitor.conf' % output_dir, 'w') as output_conf_file:
            output_conf_file.write(monitor_conf)
    return "OK"

@app.route('/ready')
def ready():
	return "OK"

copy_files()
copy_binaries()
copy_libraries()
copy_monitor_conf()