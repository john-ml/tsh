# tsh

Command-line utility. Uses an SMS gateway to communicate with a phone via text
message, allowing you to text shell commands to your computer.

### Requirements

- a phone, GMail account, and Python 3
- [less secure apps](https://myaccount.google.com/lesssecureapps) enabled

### Usage

Start tsh:
```
python tsh.py
```

Give away your personal information:
```
GMail: username
Password: hunter2 (suppressed)
Phone number (numbers only): 3141592653
Phone service: AT&T
```

That's it! tsh will text you, execute any unread texts, and await further instruction.

Try texting it `echo hello, world` or something.
