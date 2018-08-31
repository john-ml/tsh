# tsh

Command-line utility. Uses SMS/MMS gateways to communicate with a phone via GMail,
allowing you to text shell commands to your computer.

### Requirements

- a phone, GMail account, and Python 3
- [less secure apps](https://myaccount.google.com/lesssecureapps) enabled

### Usage

Start tsh:
```
python tsh.py
```

Enter some information so tsh knows how to read your emails and where to send texts:
```
Phone number (numbers only): 3141592653
Phone service: AT&T
GMail: username
Password: hunter2 (suppressed)
```

tsh will text you, execute any unread texts, and await further instruction.
