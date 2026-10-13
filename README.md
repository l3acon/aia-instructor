# AIA Instructor

Instructor toolkit for **Ansible Island Adventure** — manage your CTFd instance, deploy and update challenges, and generate participant handouts.

## Quick Start

```bash
# Clone this repo
git clone https://github.com/l3acon/aia-instructor.git
cd aia-instructor

# Set your vault password (get this from the event organizer)
echo "YOUR_VAULT_PASSWORD" > .vault-password

# Deploy challenges to your CTFd instance
ansible-playbook deploy.yml --vault-password-file .vault-password
```

## What's Inside

| Path | Purpose |
|------|---------|
| `deploy.yml` | Main deployment playbook |
| `update-challenges.yml` | Update challenges on a running CTFd instance |
| `generate-handouts.yml` | Generate participant credential handouts |
| `roles/ctfd/` | CTFd deployment and configuration role |
| `roles/ctfd/vars/challenges.yml` | Challenge definitions (categories, points, hints) |
| `roles/ctfd/vars/flags.yml` | **Vault-encrypted** flag values |
| `roles/verifier/` | Solution verification sidecar |
| `handouts/` | Handout templates and banner images |
| `solution-verification-app/` | Verifier application source |

## Managing Flags

Flags are stored in `roles/ctfd/vars/flags.yml` and encrypted with Ansible Vault.

```bash
# View flags (requires vault password)
ansible-vault view roles/ctfd/vars/flags.yml --vault-password-file .vault-password

# Edit flags
ansible-vault edit roles/ctfd/vars/flags.yml --vault-password-file .vault-password

# Re-encrypt with a new password
ansible-vault rekey roles/ctfd/vars/flags.yml --vault-password-file .vault-password
```

## Customizing Challenges

Edit `roles/ctfd/vars/challenges.yml` to modify challenge definitions. Flag values are referenced as `{{ ctfd_flags.<flag_name> }}` and resolved from the vault-encrypted file at deploy time.

After modifying challenges, re-deploy:

```bash
ansible-playbook update-challenges.yml --vault-password-file .vault-password
```

## Participant Repository

The [ansible-survival-kit](https://github.com/l3acon/ansible-survival-kit) repository is forked into each participant's Gitea account. It contains the playbooks and files participants use to solve challenges.
