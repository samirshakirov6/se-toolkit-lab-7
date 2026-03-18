# `SSH`

<h2>Table of contents</h2>

- [What is `SSH`](#what-is-ssh)
- [`SSH` key pair](#ssh-key-pair)
  - [`SSH` public key](#ssh-public-key)
  - [`SSH` private key](#ssh-private-key)
- [`sshd`](#sshd)
- [`ssh-agent`](#ssh-agent)
- [`SSH` shell](#ssh-shell)
  - [`SSH` shell prompt](#ssh-shell-prompt)
  - [Check whether you run an `SSH` shell](#check-whether-you-run-an-ssh-shell)
- [`scp`](#scp)

## What is `SSH`

`SSH` (`Secure Shell`) is a protocol used to securely connect to remote machines.

You can use it to connect to [your virtual machine](./vm.md#your-vm).

> [!IMPORTANT]
> **Windows users:** Use [`WSL`](./operating-system.md#wsl) (Windows Subsystem for Linux).
> Do not use `PowerShell`, `cmd.exe`, or `Git Bash` — the commands below are not guaranteed to work there.

## `SSH` key pair

`SSH` uses a key pair for authentication:

<!-- no toc -->
- [`SSH` public key](#ssh-public-key)
- [`SSH` private key](#ssh-private-key)

### `SSH` public key

An `SSH` public key is the shareable half of an [`SSH`](#what-is-ssh) key pair.

You give your public key to [remote hosts](./computer-networks.md#remote-host) — they store it in `~/.ssh/authorized_keys` to recognize you on future connections.

The public key file has a `.pub` extension (e.g., `se_toolkit_key.pub`).

### `SSH` private key

An `SSH` private key is the secret half of an [`SSH`](#what-is-ssh) key pair.

It stays on your local machine and is never shared. During authentication, `SSH` uses it to prove your identity without sending it over the [network](./computer-networks.md#what-is-a-network).

> [!CAUTION]
> Never share your private key. Anyone who has it can authenticate as you.

## `sshd`

`sshd` (the `SSH` daemon) is a program that runs on the [remote host](./computer-networks.md#remote-host) and [listens](./computer-networks.md#listen-on-a-port) for incoming `SSH` connections.

You do not need to configure it — your [VM](./vm.md#your-vm) already has it running.

## `ssh-agent`

`ssh-agent` is a background program that stores your private `SSH` key in memory for the duration of your session.

When `ssh-agent` holds your key, you do not need to type a passphrase every time you connect.

See [Start the `ssh-agent`](./vm-access.md#start-the-ssh-agent) for setup instructions.

## `SSH` shell

An `SSH` shell is the interactive [shell](./shell.md#what-is-a-shell) session you get after [connecting to the VM](./vm-access.md#connect-to-the-vm) over `SSH`.

Commands you run in it execute on the remote machine, not on your local computer.

### `SSH` shell prompt

A typical [`SSH` shell](./ssh.md#ssh-shell) prompt looks like:

```terminal
<user>@<host>:<directory-path>$
```

See:

- [`<user>`](./operating-system.md#user-placeholder)
- [`<host>`](./computer-networks.md#host-placeholder)
- [`<directory-path>`](./file-system.md#directory-path-placeholder)

> [!NOTE]
> The `$` at the end indicates a regular user.
> A `#` indicates [the user `root`](./linux.md#the-user-root).

### Check whether you run an `SSH` shell

1. To check whether you run an `SSH` shell,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```
   w
   ```

2. Look at the `FROM` column.

   If the value in that column:

   - is an [IP address](./computer-networks.md#ip-address), you run in an `SSH` shell.
   - `-`, you run on your local [machine](./computer-networks.md#machine) (computer).

## `scp`

`scp` (`Secure Copy`) copies [files](./file-system.md#file) between [machines](./computer-networks.md#machine) over [`SSH`](#what-is-ssh).

Common pattern:

```terminal
scp -r <local-path> <user>@<host>:<remote-path>
```

The `-r` flag copies directories recursively.
