# ZeroTrace

ZeroTrace is a powerful ethical hacking tool for anonymization, developed in Python. It helps you stay anonymous online by routing all of your system’s network traffic—not just browser traffic—through the Tor network. As a result, tracking your online activity, IP address, and location becomes extremely difficult.

---

## Features

- Sends all your internet traffic through the Tor network
- Hides your real IP address and location
- Makes it extremely difficult to track your online activity
- Lets you manually or automatically change your IP
- Shows your current Tor IP and location
- Easy to use with a beginner-friendly interface
- Works on  **Linux Distributions like `parrot os`, `ubuntu`, `kali linux`** 

---

## Requirements
- **Python 3**
- **Linux Distributions like `kali linux` , `parrot os` `ubuntu`** 
- **Tor (automatically installed if not found)**

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
4. **Run the install.py script:**
```bash
sudo python3 install.py
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
| `--auto`           | `-a`       | Auto change IP at intervals                   |
| `--time <seconds>` | `-t`       | Set interval duration (use with `--auto`)     |

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
sudo zerotrace --auto --time 300
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

**Run the install.py script**

**Then type `n` for uninstall**

---

## Author
- **Sreeraj**
- **GitHub:** https://github.com/s-r-e-e-r-a-j 

--- 

## License
This project is licensed under the MIT License.
