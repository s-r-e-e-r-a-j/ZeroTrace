# ZeroTrace

ZeroTrace is a powerful ethical hacking tool for anonymization, developed in Bash. It helps you stay anonymous online by routing all of your system’s network traffic—not just browser traffic—through the Tor network. As a result, tracking your online activity, IP address, and location becomes extremely difficult.

---

## Features

- Sends all your internet traffic through the Tor network
- Hides your real IP address and location
- Makes it extremely difficult to track your online activity
- Lets you manually or automatically change your IP
- Shows your current Tor IP and location
- Easy to use with a beginner-friendly interface
- Works on **Debian,RedHat,Arch** 

---

## Requirements
- **Gnu Bash**
- **Linux distros like Debian, RedHat, Arch** 
- **Tor, jq  and iptables (automatically installed if not found)**

---

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/s-r-e-e-r-a-j/ZeroTrace.git
```
2. **Navigate to the ZeroTrace directory:**
```bash
cd ZeroTrace
```
3. **Navigate to the ZeroTrace directory:**
```bash
cd ZeroTrace
```
4. **Run the install.sh script:**
```bash
sudo bash install.sh
```
**Then type `y` for install**

## Usage

**Run with sudo:**
```bash
sudo zerotrace [option]
```
---

## Options

| Option             | Short Form | Description                                   |
|--------------------|------------|-----------------------------------------------|
| `--start`          | `-s`       | Start routing traffic through Tor             |
| `--stop`           | `-x`       | Stop Tor and restore settings                 |
| `--ip`             | `-i`       | Show current Tor IP and location              |
| `--new-ip`         | `-n`       | Request a new identity from Tor               |
| `--auto`           | `-a`       | Auto change IP at intervals (default:500 sec) |
| `--help`           | `-h`       | show help message                             |

---

## Examples
**Start routing:**

```bash
sudo zerotrace --start
```

**Show current IP:**

```bash
sudo zerotrace --ip
```
**Request a new IP:**

```bash
sudo zerotrace --new-ip
```

**Auto change IP every 5 minutes:**

```bash
sudo zerotrace --auto 300
```

**Stop and reset:**

```bash
sudo zerotrace --stop
```
---

## Disclaimer
This tool is made only for ethical hacking, privacy, and educational use. Do not use it for illegal purposes. The author is not responsible for any misuse.

---

## Uninstallation

**Run the install.sh script**

**Then type `n` for uninstall**

---

## Author
- **Sreeraj**
- **GitHub:** https://github.com/s-r-e-e-r-a-j 

--- 

## License
This project is licensed under the MIT License.
