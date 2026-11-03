# AIA Instructor

Manage your personal **Ansible Island Adventure** CTFd board in the RHDP
facilitator-training environment. Open your Gitea clone in Dev Spaces using
`.devfile.yaml`; it supplies Ansible and the OpenShift CLI.

## Setup

1. Sign in to OpenShift as your `instructor-<guid>` account. Copy the `oc login`
   command from the console and run it in your workspace terminal.
2. In your provisioned Gitea clone, store your **provisioned lab password** in
   `.vault-password` (one line, mode `0600`). The devfile selects this path automatically. Outside Dev Spaces,
   add `--vault-password-file .vault-password` to the content commands.

These are the only instructor inputs. Organizer post-deploy re-keys each Gitea
clone's existing `roles/ctfd/vars/flags.yml` with that student's lab password,
without changing its answers. The GitHub/starter source keeps its original vault
key for organizers; use your provisioned Gitea clone for the lab. Challenge
vaults in `ansible-survival-kit` keep their own documented passphrases.

The playbooks use the current OpenShift identity and its `instructor-<guid>-ctfd` namespace. They verify the `island`
route and execute content operations inside `deploy/ctfd` using the instructor's
existing namespaced permissions. They never log in again or need cluster admin
access. If access expires, copy a fresh personal login command from the console.

## Manage challenges

```bash
# Preview content changes (database changes are rolled back)
ansible-playbook update-challenges.yml --check

# Apply YAML changes, preserving existing challenge IDs, solves, and accounts
ansible-playbook update-challenges.yml

# Reset ALL solves, submissions, awards, and purchased hints on YOUR board
# Run before playing; accounts/passwords, branding, and settings are retained
ansible-playbook deploy.yml
```

Edit `roles/ctfd/vars/challenges.yml` for categories, descriptions, points, hints,
and prerequisites. Edit encrypted answers with:

```bash
ansible-vault edit roles/ctfd/vars/flags.yml --vault-password-file .vault-password
```

Updates match challenges by name. Keep names stable to retain their IDs.
Definitions missing from YAML remain on the board; set `state: hidden` to remove
them from play. Renaming creates a new challenge. Repricing affects existing
scores, and removing a hint removes purchases of that hint. Unchanged flags and
hints keep their IDs. Base challenges are enabled by default. Advanced challenges
require a separately provisioned verifier and explicit `-e aia_enable_advanced=true`;
these playbooks do not deploy the verifier.

## Handouts

```bash
ansible-playbook generate-handouts.yml
```

This writes `handouts/generated/access.md` (ignored by Git, mode `0600`) with
service URLs and the existing training usernames. Distribute the provisioned lab
password separately using RHDP's student service details. No accounts or random
passwords are generated, and no PDF/TeX tools are required. This training board
uses one `lab-user`; a multi-participant customer event needs its own account
provisioning workflow and must not share this training account.

## Platform ownership

The leaderboard and student catalog items provision infrastructure and accounts;
the organizer's post-deploy playbook loads initial event content. Instructor
playbooks manage only their personal board. The old infrastructure role sources
remain for reference; the root playbooks do not invoke them.

The content runner targets CTFd **3.7.7**, the version provisioned by the student
CI. It validates all definitions before changes and applies content in a database
transaction. Answers travel over stdin and are suppressed from Ansible output.
It retains uploads/pages and does not restore configuration archives.

The [ansible-survival-kit](https://github.com/l3acon/ansible-survival-kit) Gitea
repository is the workspace used to solve challenges.
