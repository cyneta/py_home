# Fix Pi5 Samba Share Connection from Windows 11

## Problem
Windows 11 cannot connect to Pi5 Samba share with error:
```
System error 67 has occurred.
The network name cannot be found.
```

## What We've Verified
- ✅ All SMB ports open (445, 139, 137, 138)
- ✅ Samba running and accessible locally on Pi
- ✅ SMB2/SMB3 protocol configured on Pi
- ✅ NetBIOS name resolution working
- ✅ Port 445 reachable from Windows
- ❌ Windows cannot connect to share

## Root Cause
Windows 11 Pro after recent updates (KB5052093 and later) has a bug where it requires encrypted SMB connections but rejects unencrypted access by default, even when the server is configured correctly.

## Solution (Requires Admin PowerShell)

### Step 1: Run PowerShell as Administrator
Right-click PowerShell → Run as Administrator

### Step 2: Disable Encrypted Access Requirement
```powershell
Set-SmbServerConfiguration -RejectUnencryptedAccess $false -Force
```

### Step 3: Test Connection
```powershell
net use H: \\192.168.50.79\usb-work /user:matt.wheeler password
```

## Alternative Solutions (if Step 2 doesn't work)

### Option A: Enable SMB Encryption on Pi Samba
Add to `/etc/samba/smb.conf` under `[global]`:
```
server signing = mandatory
smb encrypt = required
```

Then restart: `sudo systemctl restart smbd`

### Option B: Flush DNS and Reset Network Stack
```powershell
ipconfig /flushdns
netcfg -d
# Reboot system
```

### Option C: Check for Hyper-V Virtual Switch Issues
Some users report this issue only occurs with Hyper-V enabled. Disable Hyper-V Virtual Switches if not needed.

## Working Pi Samba Configuration
File: `/etc/samba/smb.conf`
```
[global]
   workgroup = WORKGROUP
   server string = Pi5 Samba
   security = user
   map to guest = never
   server min protocol = SMB2
   server max protocol = SMB3
   log level = 2

[usb-work]
   path = /mnt/usb-work
   browseable = yes
   writable = yes
   guest ok = no
   valid users = matt.wheeler
   create mask = 0775
   directory mask = 0775
```

## Samba User Setup
```bash
sudo smbpasswd -a matt.wheeler
# Enter password when prompted
```

## References
- [Windows 11 can't connect to Ubuntu samba shares](https://www.elevenforum.com/t/windows-11-cant-connect-to-ubuntu-samba-shares.17645/)
- [SMB connection problem after KB5052093](https://learn.microsoft.com/en-us/answers/questions/2203058/smb-connection-problem-after-kb5052093-connection)
- [net use stopped working April 17, 2025 - System error 67](https://learn.microsoft.com/en-us/answers/questions/3869060/net-use-stopped-working-april-17-2025-for-no-reaso)

## Status
- **Created:** 2025-12-10
- **Status:** Needs admin PowerShell to complete
- **Fallback:** rsync over SSH works fine (no Samba needed)
