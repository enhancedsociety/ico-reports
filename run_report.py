#!/usr/bin/env python3

import argparse
import collections
import datetime
import os
import shutil
import subprocess
from functools import reduce

import yaml
from git import Repo

# * CAUTION *
#
# This script allows multiple configs to be provided, and as such
# many repositories or many branches of the same repository could
# in theory be analysed simultaneously. In practice, though, the
# contract cache and the header information on git assume one and
# only one repository being checked.

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', '-o', default='out',
                        help='Dir to output reports')
    parser.add_argument('configs', metavar='CONFIG',
                        nargs='+', help='yaml config file')

    args = parser.parse_args()

    SOLSA_CMD = "solsa"

    output_dir = os.path.abspath(args.output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # do not repeat analysis since it's a heavy op
    CONTRACT_CACHE = collections.defaultdict(bool)

    header_info = {
        'date': datetime.date.today().isoformat(),
        'git_commit': 'N/A',
        'git_ref': 'N/A',
        'git_origin_url': 'N/A',
    }

    dir_under_git = os.path.abspath(os.path.join(
        os.path.dirname(args.configs[0]), '..'))

    repo = Repo(dir_under_git)
    if not repo.bare and not repo.is_dirty():
        configs_untracked = reduce(
            lambda p, c: p or c in args.configs, repo.untracked_files, False)
        contracts_untracked = len(list(filter(lambda c: c.endswith(
            '.sol'), repo.untracked_files))) > 0
        if not (configs_untracked or configs_untracked):
            header_info['git_commit'] = repo.head.commit
            header_info['git_ref'] = repo.head.reference
            header_info['git_origin_url'] = repo.remotes.origin.url

    for c in args.configs:
        with open(c, 'r') as f:
            cy = yaml.safe_load(f)

            contracts = list()

            for eth_net in cy:
                if type(cy[eth_net]) is dict and 'contracts' in cy[eth_net]:
                    cl = cy[eth_net]['contracts']
                    contracts.extend([cl[x]['contract_file'] for x in cl])

            basepath = os.path.abspath(os.path.join(os.path.dirname(c), '..'))
            contracts = [
                'contracts/{}'.format(s) for s in contracts]

            for contract_file in contracts:
                # Ideally we would protect against same contract filenames
                # in different folders, but for now we will ignore that edge
                # case, for simplicity. Also, because so far it hasn't happened.
                # Still, it's better to leave this comment if it ever does.
                if contract_file not in CONTRACT_CACHE:
                    CONTRACT_CACHE[contract_file] = True
                    contract_filename = os.path.basename(contract_file)
                    # Gnosis + mythril = memory hike to infinity
                    # Burnable + mythril = memory hike to mountains
                    depth = 'deepest'
                    if contract_filename == 'GnosisWallet.sol':
                        depth= 'shallow'
                    if contract_filename == 'BurnableCrowdsaleToken.sol':
                        depth= 'deep'
                    shutil.copyfile(os.path.join(basepath, contract_file), os.path.join(
                        output_dir, contract_filename))
                    output_file = os.path.join(output_dir, '{}.{}'.format(
                        contract_filename, 'html'))
                    print('Writing {} report to {}'.format(
                        contract_file, output_file))
                    cmd = subprocess.run(
                        [SOLSA_CMD, "-d", depth, "-f",
                            contract_file, "-o", output_file, "-i"],
                        cwd=basepath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if cmd.returncode != 0:
                        print(cmd.stdout)
                        print(cmd.stderr)

    # now we create an index for all the contracts
    def make_li(contract_path):
        s = os.path.basename(contract_path)
        r_href = '{}.html'.format(s)
        label = os.path.splitext(s)[0]
        return r'''
      <div class="card">
        <h3>{}</h3>
        <hr>
        <div class="container">
          <p><a href="{}">Report</a></p>
          <p><a href="{}">Source</a></p>
        </div>
      </div>'''.format(label, r_href, s)

    LINKS = [make_li(c) for c in sorted(CONTRACT_CACHE.keys())]

    HEAD = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Solsa Reports</title>
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        main {
            display: flex;
            width: 90%;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        .card {
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            transition: 0.3s;
            padding: 2px 16px;
            width: 20vw;
            min-width: 100px;
            max-width: 300px;
            margin-bottom: 16px;
        }
        .card>h3 {
            text-overflow: ellipsis;
            overflow: hidden;
        }
        .card:hover {
            box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
        }
        .container {
            padding: 2px 16px;
        }
    </style>
  </head>'''+'''
  <body>
    <header>
      <h1>Solsa Reports</h1>
      <h5>{date}</h5>
      <hr>
      <aside>
        <h4>git info</h4>
        <p>Repository URL {git_origin_url}</p>
        <p>Branch {git_ref}</p>
        <p>Commit {git_commit}</p>
      </aside>
    </header>
    <main>
'''.format(**header_info)

    TAIL = '''
    </main>
  </body>
</html>
'''
    with open(os.path.join(output_dir, 'index.html'), 'w') as f:
        f.write('{}{}{}'.format(HEAD, ''.join(LINKS), TAIL))

    print('Successfully generated reports to {}'.format(output_dir))
