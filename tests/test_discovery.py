"""Exercise actual Ansible discovery with an oc fixture and rejected identities."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('ansible-playbook'), 'ansible-playbook required')
class Discovery(unittest.TestCase):
    def run_discovery(self, identity='instructor-one', namespace='instructor-one-ctfd', service='ctfd'):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            fake=root/'oc'
            fake.write_text('''#!/usr/bin/env python3
import os,sys,json
args=sys.argv[1:]
with open(os.environ['AIA_READS'],'a') as f:f.write(json.dumps(args)+'\\n')
if args==['whoami']: print(os.environ['AIA_IDENTITY'])
elif args==['get','route','island','-n','instructor-one-ctfd','-o','json']:
 print(os.environ['AIA_ROUTE'])
else:sys.exit(1)
''')
            fake.chmod(0o700)
            (root/'play.yml').write_text(json.dumps([dict(hosts='localhost',gather_facts=False,
                tasks=[{'ansible.builtin.import_tasks':str(Path(__file__).parents[1]/'tasks/discover.yml')}])]))
            env=dict(os.environ,PATH=t+':'+os.environ['PATH'],AIA_IDENTITY=identity,AIA_READS=str(root/'reads'),
                AIA_ROUTE=json.dumps(dict(metadata=dict(namespace=namespace),spec=dict(to=dict(name=service),
                       host='island-instructor-one-ctfd.apps.test.invalid',tls=dict(termination='edge')))),
                ANSIBLE_CONFIG=str(root/'ansible.cfg'),ANSIBLE_NOCOLOR='1')
            env.pop('ANSIBLE_VAULT_PASSWORD_FILE',None)
            (root/'ansible.cfg').write_text('[defaults]\nstdout_callback=default\n')
            r=subprocess.run(['ansible-playbook',str(root/'play.yml')],env=env,capture_output=True,text=True,timeout=40)
            return r.returncode,r.stdout+r.stderr,(root/'reads').read_text()

    def test_personal_route_requires_only_namespaced_read(self):
        rc,output,reads=self.run_discovery()
        self.assertEqual(rc,0,output)
        self.assertEqual(len(reads.splitlines()),2)
        self.assertNotIn('gitea',reads)

    def test_admin_and_service_accounts_rejected_before_resource_access(self):
        for identity in ('admin','system:admin','system:serviceaccount:default:test'):
            rc,output,reads=self.run_discovery(identity=identity)
            self.assertNotEqual(rc,0,output)
            self.assertEqual(reads.strip(),'["whoami"]')

    def test_other_namespace_rejected(self):
        rc,output,_=self.run_discovery(namespace='instructor-two-ctfd')
        self.assertNotEqual(rc,0,output)

    def test_other_service_rejected(self):
        rc,output,_=self.run_discovery(service='other-service')
        self.assertNotEqual(rc,0,output)
