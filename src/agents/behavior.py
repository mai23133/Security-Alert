"""Versioned, offline behavior checks derived from pinned ATT&CK concepts.

These are conservative rules, not a general semantic model or a calibrated
probability estimate. Unsupported behaviors abstain. No evaluation text is
loaded here; rules can only score an ID already supplied by a caller.
"""
from __future__ import annotations

import re

VERSION = "behavior-rules-v3"
AMBIGUOUS = re.compile(r"\b(may|might|could|possible|possibly|unclear|uncertain|suspected|potential|unconfirmed|unidentified|unspecified|insufficient|unknown|inconclusive|cannot determine|cannot be confirmed|could not be confirmed|not confirmed|not recorded|not captured|missing details|incomplete (?:evidence|telemetry|source|pattern)|(?:evidence|telemetry|source|pattern)(?: data)? (?:was )?incomplete)\b", re.I)
INJECTION = re.compile(
    r"\b("
    r"(?:ignore|disregard|override)\b.{0,80}\b(?:instructions?|rules?|previous|system)"
    r"|(?:reveal|show|print|repeat)\b.{0,60}\b(?:system\s*prompt|hidden\s*instructions?)"
    r"|return\s+(?:technique_id\s*[\"']?\s*)?T\d{4}(?:\.\d{3})?"
    r"|system\s*prompt"
    r"|assistant\s*:"
    r"|output\s+(?:only\s+)?T\d{4}(?:\.\d{3})?"
    r"|you\s+are\s+now\b.{0,60}\b(?:assistant|developer|system|mode)"
    r")",
    re.I | re.S,
)
BENIGN = re.compile(r"\b(authorized|approved|routine maintenance|patch[ -]management|training|simulation|benign|health[ -]check|no malicious activity|legitimate maintenance)\b", re.I)
NEGATED = re.compile(r"\b(no evidence of|did not|does not|was not (?:execut\w*|observed|detected|launched)|were not (?:execut\w*|observed|detected|launched)|never|without (?:execut\w*|running|launch\w*|dump\w*|steal\w*|access\w*)|not observed|not executed|no (?:powershell|credential|brute|script|command))\b", re.I)
ACTION = r"\b(execut\w*|ran|run\w*|launch\w*|invok\w*|spawn\w*|abus\w*|download\w*|load\w*|open\w*|steal\w*|stole|extract\w*|dump\w*|captur\w*|read|access\w*|attempt\w*|exploit\w*|sent|receiv\w*|deliver\w*|creat\w*|modif\w*|schedul\w*|collect\w*|obtain\w*)\b"

# Each tuple requires ALL patterns in one observed clause. Alternatives remain
# explicit; no narrative-wide bag of words is accepted as behavior evidence.
RULES: dict[str, tuple[str, ...]] = {
    "T1059.001": (r"\b(powershell|pwsh)(?:\.exe)?\b", ACTION),
    "T1059.003": (r"\b(cmd\.exe|command (?:prompt|shell)|cmd /c)\b", ACTION),
    "T1059.004": (r"\b(bash|zsh|/bin/sh|unix shell|shell script)\b", ACTION),
    "T1059.005": (r"\b(vbscript|visual basic|vba|wscript|cscript)\b", ACTION),
    "T1059.006": (r"\bpython(?:3|\.exe)?\b", ACTION),
    "T1059.007": (r"\b(javascript|jscript|node\.js)\b", ACTION),
    "T1110": (r"\b(brute[ -]force|(?:multiple|repeated|hundreds|thousands|\d{2,})\b.{0,50}\bfailed|failed\b.{0,50}\b(?:attempts|logins))", r"\b(password\w*|login\w*|logon\w*|authentication|rdp|ssh)\b"),
    "T1110.001": (r"\b(guess\w*|dictionary)\b", r"\bpassword\w*\b"),
    "T1110.002": (r"\b(crack\w*|hashcat|john the ripper)\b", r"\b(hash\w*|password\w*)\b"),
    "T1110.003": (r"\b(spray\w*|one password|same password|single password)\b", r"\b(accounts|users|usernames)\b"),
    "T1110.004": (r"\b(stuffing|leaked|breached|stolen)\b", r"\b(credential pairs|username.password|password pairs|credentials)\b", r"\b(login|logins|attempt\w*|reus\w*|stuffing)\b"),
    "T1003": (r"\b(credential dumping|dump\w*\b.{0,40}\bcredentials)\b",),
    "T1003.001": (r"\b(lsass|lsass\.exe)\b", r"\b(dump\w*|memory|read|access\w*|procdump)\b"),
    "T1003.002": (r"\b(sam|security account manager)\b", r"\b(dump\w*|save|cop\w*|extract\w*|hash\w*)\b"),
    "T1003.003": (r"\bntds(?:\.dit)?\b", r"\b(dump\w*|cop\w*|extract\w*|vssadmin|shadow|access\w*)\b"),
    "T1003.006": (r"\b(dcsync|directory replication|replicat\w*\b.{0,40}\b(?:credentials|secrets))\b",),
    "T1003.008": (r"/etc/(?:shadow|passwd)", r"\b(read|cop\w*|access\w*|extract\w*|dump\w*|cat|stole)\b"),
    "T1047": (r"\b(wmi|wmic|windows management instrumentation)\b", r"\b(process|execut\w*|spawn\w*|creat\w*|invoke\w*)\b"),
    "T1053.003": (r"\b(cron|crontab)\b", r"\b(job|entry|schedul\w*|execut\w*|creat\w*|modif\w*)\b"),
    "T1053.005": (r"\b(schtasks|scheduled task|task scheduler)\b", ACTION),
    "T1053.006": (r"\b(systemd|\.timer)\b", r"\b(timer|schedul\w*)\b", ACTION),
    "T1566.001": (r"\b(email|mail|phishing|message)\b", r"\b(attachment|attached|document|spreadsheet)\b", r"\b(malicious|suspicious|phish\w*|lure|spoof\w*|weaponized)\b"),
    "T1566.002": (r"\b(email|mail|phishing|message)\b", r"\b(link|url)\b", r"\b(malicious|suspicious|phish\w*|lure|spoof\w*)\b"),
    "T1204.001": (r"\b(user|employee|victim)\b", r"\b(click\w*|open\w*)\b", r"\b(link|url)\b", r"\b(malicious|suspicious|phish\w*)\b"),
    "T1204.002": (r"\b(user|employee|victim)\b", r"\b(open\w*|execut\w*|enabl\w*)\b", r"\b(file|attachment|document|spreadsheet|macro\w*|malicious content)\b", r"\b(malicious|suspicious|macro\w*|malicious content)\b"),
    "T1190": (r"\b(exploit\w*|vulnerability|remote code execution|sql injection)\b", r"\b(public.facing|internet.facing|web server|web application|vpn gateway|external application)\b"),
    "T1189": (r"\b(browser|website|web page)\b", r"\b(exploit\w*|drive.by|compromised)\b", ACTION),
    "T1078": (r"\b(stolen|compromised|valid)\b", r"\b(account\w*|credentials)\b", r"\b(login|logon|logged|authenticated|access\w*|used)\b"),
    "T1133": (r"\b(vpn|rdp|ssh|remote service\w*)\b", r"\b(external|internet|remote)\b", r"\b(access\w*|login|logged|authenticated|connect\w*)\b"),
    "T1558.003": (r"\b(kerberoast\w*|service tickets?|tgs)\b", r"\b(request\w*|crack\w*|extract\w*|roast\w*)\b"),
    "T1558.004": (r"\b(as.rep|pre.authentication|preauthentication)\b", r"\b(roast\w*|disabled|without|request\w*)\b"),
    "T1558.001": (r"\b(golden ticket|krbtgt)\b", r"\b(forg\w*|creat\w*|stolen|hash)\b"),
    "T1552.001": (r"\b(credential\w*|password\w*|secret\w*)\b", r"\b(config\w*|files?|plaintext|plain.text)\b", ACTION),
    "T1552.003": (r"(\.bash_history|shell history|command history)", ACTION),
    "T1552.004": (r"(private key|id_rsa|\.pem\b)", ACTION),
    "T1555.003": (r"\b(browser|chrome|firefox|login data)\b", r"\b(password\w*|credential\w*)\b", r"\b(steal\w*|stole|extract\w*|decrypt\w*|read|dump\w*)\b"),
    "T1056.001": (r"\b(keylog\w*|keystrokes|keyboard input)\b", r"\b(captur\w*|record\w*|log\w*|hook\w*|collect\w*)\b"),
    "T1040": (r"\b(tcpdump|wireshark|sniff\w*|packet\w*)\b", r"\b(captur\w*|sniff\w*|collect\w*|intercept\w*)\b"),
    "T1539": (r"\b(session cookies?|web cookies?)\b", r"\b(steal\w*|stole|extract\w*|cop\w*|hijack\w*)\b"),
    "T1621": (r"\b(mfa|multi.factor|push)\b", r"\b(fatigue|repeated|flood\w*|bomb\w*)\b", r"\b(requests|prompts|notifications)\b"),
    "T1557.001": (r"\b(llmnr|nbt.ns|smb relay|name resolution)\b", r"\b(poison\w*|relay\w*|spoof\w*)\b"),
    "T1569.002": (r"\b(psexec|service control manager|sc\.exe|service)\b", r"\b(execut\w*|start\w*|launch\w*)\b"),
    "T1127.001": (r"\bmsbuild(?:\.exe)?\b", ACTION),
}
# Additional forms from the same STIX definitions, exercised on development
# cases for passive voice, command lines, protocols, and user interaction.
ALTERNATIVES = {
    "T1110": [(r"\b(failed|failures|unsuccessful|rejected)\b", r"\b(authenticat\w*|login\w*|logon\w*|sign.ins?|password\w*)\b", r"\b(repeated\w*|many|numerous|several|multiple|burst|high.volume|rapid|hundreds|thousands|\d{2,})\b")],
    "T1110.001": [(r"\b(passwords|password guesses|password list|common passwords)\b", r"\b(try\w*|tried|attempt\w*|test\w*|guess\w*|cycling)\b", r"\b(one|single|same|targeted)\b.{0,30}\b(account|user|username)\b")],
    "T1059": [(r"\b(command interpreter|scripting interpreter|command.line interpreter|shell interpreter)\b", ACTION)],
    "T1059.003": [(r"\b(cmd(?:\.exe)?\s+/(?:c|k)|\.bat\b|batch (?:file|script))", r"\b(command.line|process|ran|run|start\w*|execut\w*|launch\w*)\b")],
    "T1566.001": [(r"\b(email|mail|phish\w*)\b", r"\b(attach\w*|document|spreadsheet)\b", r"\b(macro\w*|payload|execut\w*|spoof\w*|impersonat\w*)\b")],
    "T1204.002": [(r"\b(user|employee|victim|recipient)\b", r"\b(open\w*|execut\w*|double.click\w*|click\w*)\b", r"\b(attach\w*|document|file|executable|program)\b", r"\b(untrusted|unknown|unsigned|download\w*|malicious|suspicious|payload|macro\w*)\b")],
    "T1190": [(r"\b(public|external|internet.facing|exposed|web)\b", r"\b(application|server|service|endpoint|portal)\b", r"\b(exploit\w*|crafted|injection|vulnerab\w*|payload)\b")],
    "T1189": [(r"\b(browser|browsing|website|web page)\b", r"\b(visit\w*|brows\w*|redirect\w*)\b", r"\b(exploit\w*|malicious|compromised|payload|infect\w*)\b")],
    "T1133": [(r"\b(vpn|citrix|remote.access gateway|external remote service)\b", r"\b(login|logon|signed|logged|connect\w*|access\w*|session|authenticat\w*)\b", r"\b(stolen|compromised|suspicious|unexpected|unknown|external|attacker|intruder)\b")],
    "T1078": [(r"\b(account|credentials|username|password)\b", r"\b(successful|successfully|authenticated|signed in|logged in|logged on)\b", r"\b(unusual|unexpected|suspicious|unknown|stolen|compromised|attacker|intruder|abnormal)\b")],
    "T1555.003": [(r"\b(browser|chrome|firefox)\b", r"\b(login data|saved passwords|credential\w*|password database)\b", r"\b(cop\w*|open\w*|quer\w*|export\w*|decrypt\w*|read|access\w*)\b")],
    "T1091": [(r"\b(usb|removable|thumb drive|flash drive)\b", r"\b(autorun|malware|infect\w*|malicious|payload)\b", r"\b(execut\w*|cop\w*|spread\w*|launch\w*|insert\w*|replicat\w*)\b")],
    "T1106": [(r"\b(native api|ntcreateprocess|createprocess|createthread|ntcreatethreadex|syscalls?|system calls?)\b", r"\b(call\w*|invok\w*|execut\w*|creat\w*|launch\w*|start\w*)\b")],
    "T1204.004": [(r"\b(copy|copied|paste\w*|clickfix)\b", r"\b(command|code|script)\b", r"\b(user|victim|employee|captcha|run dialog|terminal)\b")],
}
# Protocol names and authentication attempts can establish password guessing
# even when the narrative does not repeat the word 'password'.
ALTERNATIVES["T1110.001"].append((r"\b(guess\w*|dictionary)\b", r"\b(ssh|rdp|login|authentication|account)\b", r"\b(attempt\w*|try\w*|tried|repeat\w*|test\w*)\b"))
ALTERNATIVES["T1059"].append((r"\b(interpreter|shell)\b", r"\b(command\w*|script\w*)\b", r"\b(execut\w*|ran|launch\w*|invok\w*|spawn\w*)\b"))
ALTERNATIVES["T1566.001"].append((r"\b(email|mail|message)\b", r"\b(attach\w*|document|spreadsheet)\b", r"\b(spearphish\w*|quarantin\w*|trojan\w*|deceptive|social engineering)\b"))
ALTERNATIVES["T1566.001"].append((r"\b(mail|email) gateway\b", r"\b(deliver\w*|receiv\w*)\b", r"\b(targeted|malicious|suspicious|weaponized)\b", r"\b(attach\w*|archive|\.zip\b|\.docm\b|\.xlsm\b)"))
ALTERNATIVES["T1566.001"].append((r"\b(receiv\w*|deliver\w*)\b", r"\.(?:docm|xlsm|pptm|zip)\b", r"\b(attach\w*|targeted|malicious|payload|macro\w*)\b"))
ALTERNATIVES["T1133"].append((r"\b(remote services?|remote access|remote desktop|vpn|citrix|vnc|winrm)\b", r"\b(external|internet|exposed|gateway)\b", r"\b(sign.in|log.in|authenticat\w*|session|connect\w*|access\w*)\b"))
ALTERNATIVES["T1133"].append((r"\b(remote administration service|remote management service|vpn|remote access)\b", r"\b(external|exposed|internet)\b", r"\b(accept\w*|enter\w*|establish\w*|session|connect\w*|access\w*)\b"))
ALTERNATIVES["T1078"].append((r"\b(stolen|compromised|valid)\b", r"\b(account\w*|credentials)\b", r"\b(sign.in|log.in|authenticat\w*|session|connect\w*)\b"))
ALTERNATIVES["T1078"].append((r"\b(stolen|compromised|valid|correct)\b", r"\b(account\w*|credentials)\b", r"\b(enter\w*|accept\w*|login|logon|session|connect\w*|access\w*|used?)\b"))
ALTERNATIVES["T1091"].append((r"\b(usb|removable|thumb drive|flash drive)\b", r"\b(autorun|auto.run|automatically|auto.launch\w*)\b", r"\b(execut\w*|launch\w*|start\w*)\b"))
ALTERNATIVES["T1091"].append((r"\b(usb|removable|thumb drive|flash drive)\b", r"\b(worm\w*|malware|payload|infect\w*)\b", r"\b(cop\w*|execut\w*|launch\w*|spread\w*|start\w*)\b"))
# Bind the actor to the interaction. A trailing phrase such as "downloaded by
# the user" must not turn a process launch into User Execution.
ALTERNATIVES["T1204.002"].append((r"\b(user|employee|victim|staff|recipient)\b.{0,45}\b(open\w*|click\w*|launch\w*|execut\w*)\b", r"\.(?:exe|scr|docm|xlsm|lnk)\b", r"\b(malicious|untrusted|download\w*|payload|dump\w*|spawn\w*|after which)\b"))
ALTERNATIVES["T1204.002"].append((r"\b(opened|opening|double.clicked|executed)\b", r"\b(malicious|untrusted|weaponized)\b", r"\b(attach\w*|document|file|\.docm\b|\.xlsm\b)"))
ALTERNATIVES["T1190"].append((r"\b(web|http) (?:process|service|worker)\b", r"\b(crafted|malformed|exploit\w*)\b.{0,25}\b(request|payload)\b", r"\b(crash\w*|spawn\w*|execut\w*|child process)\b"))
# Service execution needs a service-control operation; mere references to a
# process or 'service' alongside WMI do not establish this separate behavior.
RULES["T1569.002"] = (r"\b(psexec|service control manager|sc\.exe|startservice\w*|service (?:was )?(?:created|started))\b", r"\b(execut\w*|start\w*|launch\w*|creat\w*)\b")
COMPILED = {key: [tuple(re.compile(p, re.I) for p in patterns)] for key, patterns in RULES.items()}
for _key, _variants in ALTERNATIVES.items():
    COMPILED.setdefault(_key, []).extend(tuple(re.compile(p, re.I) for p in variant) for variant in _variants)


def clauses(narrative: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?;])\s+|\s+but\s+|\s+however[,]?\s+", narrative, flags=re.I) if part.strip()]


def prompt_injection_detected(narrative: str) -> bool:
    """Conservatively detect instruction-like text before any provider call.

    This is a deterministic preflight guard, not a claim that arbitrary prompt
    injection can be classified perfectly. A match causes the whole request to
    fail closed instead of attempting to sanitize and continue.
    """
    return bool(INJECTION.search(narrative))


def safe_clause(span: str) -> bool:
    # 'without preauthentication' describes AS-REP roasting, not negation.
    checked = re.sub(r"without pre.?authentication", "preauthentication disabled", span, flags=re.I)
    # Negated authorization is suspicious context, not evidence that an action
    # was benign: "no approved deployment" and "not authorized" must not be
    # classified like "approved deployment" or "authorized activity".
    checked = re.sub(
        r"\b(?:no|not|without)\s+(?:an?\s+)?(?:approved|authorized)\b",
        "unapproved",
        checked,
        flags=re.I,
    )
    return not (INJECTION.search(checked) or BENIGN.search(checked) or NEGATED.search(checked))


def support(technique_id: str, span: str, name: str = "") -> float:
    if not safe_clause(span):
        return 0.0
    patterns = COMPILED.get(technique_id)
    if patterns is not None:
        # Normalize conventional spelling/role variants only for matching;
        # evidence still returns verbatim text and offsets from the alert.
        normalized = re.sub(r"\be-mail\b", "email", span, flags=re.I)
        normalized = re.sub(r"\b(staff|recipient|operator)\b", "user", normalized, flags=re.I)
        matched = any(all(pattern.search(normalized) for pattern in variant) for variant in patterns)
        return (0.60 if AMBIGUOUS.search(span) else 0.82) if matched else 0.0
    # Fallback requires the complete canonical name AND an observed action.
    # Low confidence forces review for behaviors without an explicit rule.
    if name and re.search(r"\b" + re.escape(name) + r"\b", span, re.I) and re.search(ACTION, span, re.I):
        return 0.55
    return 0.0


def evidence(narrative: str, technique_id: str, name: str = "") -> list[str]:
    return [span for span in clauses(narrative) if support(technique_id, span, name)]


def contextual_span_valid(narrative: str, span: str, technique_id: str, name: str) -> bool:
    # Checking the whole enclosing clause prevents extracting 'executed
    # PowerShell' from 'never executed PowerShell' to manufacture evidence.
    return bool(span and span in narrative and support(technique_id, span, name) and any(
        span in clause and safe_clause(clause) for clause in clauses(narrative)
    ))
