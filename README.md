# SSH Tunnel Manager

A cross-platform GUI application for creating and managing SSH tunnels through bastion hosts. Built with Python and Tkinter.

## Features

- **Cross-Platform** — works on Windows, Linux, and macOS
- **Multiple Tunnels** — create and manage multiple SSH tunnels simultaneously
- **Save & Load Configurations** — persist tunnel setups as JSON files
- **Auto-Load on Startup** — automatically loads the latest saved configuration and creates tunnels
- **Auto Host Key Acceptance** — new bastion hosts are accepted automatically (uses `StrictHostKeyChecking=accept-new`, so changed keys are still rejected for security)
- **Real-Time Status** — active tunnels list with PID tracking and log output
- **Context Menu** — right-click on tunnels to stop them individually

## Requirements

- Python 3.6+
- Tkinter (usually included with Python)
- OpenSSH client

### Installing Tkinter

**Windows:** Included with Python by default. If missing, reinstall Python from [python.org](https://python.org) with the "tcl/tk" option checked.

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL/CentOS
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

**macOS:** Included with Python. If using Homebrew: `brew install python-tk`

### Installing OpenSSH Client

**Windows 10/11:** Usually pre-installed. If not: Settings → Apps → Optional Features → OpenSSH Client.

**Linux:** Usually pre-installed. If not: `sudo apt-get install openssh-client` (Debian/Ubuntu) or `sudo dnf install openssh-clients` (Fedora/RHEL).

**macOS:** Pre-installed by default.

## Usage

```bash
python3 tunnel-manager.py
```

### Quick Start

1. **Bastion Host** — enter in `username@hostname` format (e.g. `ec2-user@YOUR_BASTION_IP`)
2. **Private Key** — click "Browse..." to select your `.pem` key file
3. **Tunnel Config** — set local port, remote IP, and remote port
4. **Create Tunnel** — click the button and check the log for status

After the tunnel is created, connect to the remote service via `localhost:<local_port>`.

### Example: RDP Through a Bastion

| Field       | Value              |
|-------------|--------------------|
| Bastion     | `ec2-user@YOUR_BASTION_IP` |
| Private Key | `/path/to/key.pem` |
| Local Port  | `3391`             |
| Remote IP   | `REMOTE_IP`        |
| Remote Port | `3389`             |

Then connect via RDP to `localhost:3391`.

### Saving & Loading Configurations

- **Save Configuration** — saves all active tunnels to a JSON file
- **Load Configuration** — loads a previously saved config and optionally creates all tunnels
- **Auto-Load** — on startup, the app searches for the latest config file in common locations (`~/Documents`, `~/`, script directory) and auto-creates tunnels

See [`tunnel_config_example.json`](tunnel_config_example.json) for the config file format.

## Configuration File Format

```json
{
    "bastion_host": "ec2-user@YOUR_BASTION_IP",
    "key_file": "/path/to/your/private-key.pem",
    "tunnels": [
        {
            "local_port": 3391,
            "remote_ip": "REMOTE_IP_1",
            "remote_port": 3389
        },
        {
            "local_port": 3392,
            "remote_ip": "REMOTE_IP_2",
            "remote_port": 3389
        }
    ]
}
```

## Troubleshooting

**Port conflict** — each tunnel needs a unique local port. Check the Active Tunnels list.

**Key file permissions** — on Linux/macOS, ensure `chmod 600 /path/to/key.pem`.

**Tunnel shows "Active" but doesn't work** — verify the remote IP/port are correct and the target service is running.

**Connection refused** — check that the bastion host is reachable and your key has access.

## Platform Notes

| Platform | Tunnel Background | Context Menu |
|----------|-------------------|--------------|
| Windows  | Hidden console window (`CREATE_NO_WINDOW`) | Right-click |
| Linux    | New session (detached) | Right-click |
| macOS    | New session (detached) | Ctrl+Click or Right-click |

## License

MIT License — see [LICENSE](LICENSE) for details.

## Author

Created by Oleh Sharudin
