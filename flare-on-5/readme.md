## FireEye FLARE-On 5 Write-ups

Flare-On #5 had an amazing collection of challenges demonstrating various malware techniques
and some pretty arcane Windows internals, not to mention [@nickharbour]'s special brand of evil.
In typical Flare-On style, they were served with a side a houmor and sprinkled with a
generous helping of general smack-talk. All told, Flare-On #5 was an awesome experience!

All challenges were very well engineered and must have taken the authors a significant amount of
time to build and test. Thank you [@fireeye], [@nickharbour], [@m_r_tz], [@spresec], [@williballenthin],
Sebastian Vogl, Ryan Warns, [0xmwilliams], [@mykill], [@jay_smif], [@mikesiko].

The write-ups mainly follow the route I took in solving the challenges (#5 being the exception) and 
also explore some alternative approaches. I am releasing (under GPL) the source code for the tools
I threw together, but bear in mind that they were 'developed' under extreme time pressure, hence
may be harder to understand than some of the challenge binaries.

If you have not looked at the actual challanges then I suggest that you open
IDA and follow my steps through the code, I suspect you'll find the write-ups easier to understand 
with that approach.

Enjoy the journey,

[@eleemosynator]


Tools
----
- [CFF Explorer Suite][CFF]: CFF Explorer (Explorer Suite) - Graphical PE file parser with built-in Resource and Hex Editors
- [HxD][HxD]: Fast and simple Hex Editor
- [IDA Pro][IDA]: The best disassembler money can buy (there is a free edition of v7.0)
- [IDAPython][IDAPython]: Python scripting framework for IDA Pro
- [Virtual Box][VBox]: Free Virtual Machine platform
- [Wireshark][Wireshark] for tracking specific TCP streams
- [NetworkMiner][NetworkMiner] for initial traffic classification
- [JSNice][JSNice]: Online Javascript prettyfier
- [dotNetSpy][dnSpy]: .NET reverse engineering framework with built-in debugger and much more
- [cfr][cfr]: Command-line based Java decompiler, by [Lee Benfield][LeeAtBenf]
- [JD][JD]: Java decompiler with GUI and IDE integration
- [sysinternals][sysinternals]: Excellent collection of utilities for analyzing windows internals
- [FlareVM][FlareVM]: Installation script for an excellent collection of tools that every analysis VM needs
- [de4dot][de4dot]: .NET deobfuscation tool
- [Flare-FLOSS][floss]: String scanner on steroids (can do stack strings and some encrypted), courtesy of the FLARE team
- [signsrch]: signsrch by Luigi Auriemma: scan binaries for signature of standard crypto implenetations
- [stegsolve]: stegsolve by Caesum: Good tool for tackling steganographic image challenges


Python Packages
----
- [PyCrypto][PyCrypto]: Crypto modules for Python
- [Pillow][Pillow]: Python image manipulation library
<!--
- pefile
- dpkt
- unicorn
- capstone
- keystone
-->

Status
----

Challenge|Status
---------|---------
01 - Minesweeper Championship Registration|COMPLETE
02 - Ultimate Minesweeper|COMPLETE
03 - FLEGGO|COMPLETE
04 - binstall|TODO
05 - Web 2.0|TODO
06 - Magic|TODO
07 - WOW|TODO
08 - Doogie Hacker|TODO
09 - golf|TODO
10 - leet editr|TODO
11 - malware skillz|TODO
12 - Suspicious Floppy Disk|IN PROGRESS


References
---

- RC4 Encryption algorithm: [https://en.wikipedia.org/wiki/RC4][RC4], accessed 01-Oct-2018


[CFF]:http://www.ntcore.com/exsuite.php
[HxD]:https://mh-nexus.de/en/hxd/
[IDA]:https://www.hex-rays.com/products/ida/support/download.shtml
[VBox]:https://www.virtualbox.org/wiki/Downloads
[JSNice]:http://www.jsnice.org/
[FFDec]:https://www.free-decompiler.com/flash/
[NetworkMiner]:http://www.netresec.com/?page=NetworkMiner
[Wireshark]:https://www.wireshark.org/
[pcap-parser]:https://pypi.python.org/pypi/pcap-parser
[IDAPython]:https://github.com/idapython
[CFR]:http://www.benf.org/other/cfr/
[JD]:http://jd.benow.ca/
[dnSpy]:https://github.com/0xd4d/dnSpy
[de4dot]:https://github.com/0xd4d/de4dot
[sysinternals]:https://docs.microsoft.com/en-us/sysinternals/downloads/
[FlareVM]:https://github.com/fireeye/flare-vm
[floss]:https://github.com/fireeye/flare-floss
[signsrch]:https://aluigi.altervista.org/mytoolz.htm
[stegsolve]:http://www.caesum.com/handbook/stego.htm

[PyCrypto]:https://pypi.python.org/pypi/pycrypto
[Pillow]:https://python-pillow.org/

[LeeAtBenf]:https://twitter.com/LeeAtBenf
[RC4]:https://en.wikipedia.org/wiki/RC4

[@nickharbour]:https://twitter.com/nickharbour
[@fireeye]:https://twitter.com/fireeye
[@m_r_tz]:https://twitter.com/m_r_tz
[@spresec]:https://twitter.com/spresec
[@williballenthin]:https://twitter.com/williballenthin
[0xmwilliams]:https://twitter.com/0xmwilliams
[@mykill]:https://twitter.com/mykill
[@jay_smif]:https://twitter.com/jay_smif
[@mikesiko]:https://twitter.com/mikesiko
[@eleemosynator]:https://twitter.com/eleemosynator
