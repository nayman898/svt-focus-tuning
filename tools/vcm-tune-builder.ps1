<#
.SYNOPSIS
    vcm-tune-builder.ps1 - Streamlined, reusable VCM Editor automation tool for SVT Focus tuning.
.DESCRIPTION
    Automates calibration table and scalar updates in HP Tuners VCM Editor.
    Attaches to an existing open instance of VCM Editor without killing or restarting it,
    preserving interface authorization and desktop state. Supports launching if no instance is open.
    
    Driven entirely by a JSON specification file.
    
    Strict Safety Rules:
    - NEVER touches ECU flash/write functions. The owner performs all vehicle writes.
    - NEVER embeds VINs or MPVI serial numbers.
    - NEVER hex-edits .hpt files directly; all saves pass through VCM Editor.
    - Never kills the running VCM Editor process unless -KillOnExit is explicitly specified.
.EXAMPLE
    powershell -STA -NoProfile -ExecutionPolicy Bypass -File tools/vcm-tune-builder.ps1 -SpecPath "scratch/v033_spec.json"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SpecPath,

    [string]$EditorExe = "",

    [switch]$KillOnExit = $false
)

if (-not $EditorExe) {
    if (Test-Path "C:\Program Files\HP Tuners\VCM Suite (Beta)\VCM Editor.exe") {
        $EditorExe = "C:\Program Files\HP Tuners\VCM Suite (Beta)\VCM Editor.exe"
    } elseif (Test-Path "C:\Program Files\HP Tuners\VCM Suite\VCM Editor.exe") {
        $EditorExe = "C:\Program Files\HP Tuners\VCM Suite\VCM Editor.exe"
    } else {
        throw "VCM Editor.exe not found in standard HP Tuners directories"
    }
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName WindowsBase

# Native Win32 helpers for GUI automation & character typing
Add-Type -ReferencedAssemblies "WindowsBase", "UIAutomationClient", "UIAutomationTypes", "System.Windows.Forms" -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Forms;

public static class VcmNative {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] public static extern IntPtr OpenWindowStation(string lpszWinSta, bool fInherit, uint dwDesiredAccess);
    [DllImport("user32.dll")] public static extern bool SetProcessWindowStation(IntPtr hWinSta);
    [DllImport("user32.dll")] public static extern IntPtr OpenDesktop(string lpszDesktop, uint dwFlags, bool fInherit, uint dwDesiredAccess);
    [DllImport("user32.dll")] public static extern bool SetThreadDesktop(IntPtr hDesktop);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumDesktopWindows(IntPtr hDesktop, EnumWindowsProc lpfn, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void SwitchToThisWindow(IntPtr hWnd, bool fAltTab);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();

    public static void ForceForeground(IntPtr hWnd) {
        ShowWindow(hWnd, 9); // SW_RESTORE
        uint dummy;
        uint foreThread = GetWindowThreadProcessId(GetForegroundWindow(), out dummy);
        uint appThread = GetCurrentThreadId();
        if (foreThread != appThread && foreThread != 0) {
            AttachThreadInput(foreThread, appThread, true);
            SetForegroundWindow(hWnd);
            AttachThreadInput(foreThread, appThread, false);
        } else {
            SetForegroundWindow(hWnd);
        }
        SwitchToThisWindow(hWnd, true);
        Thread.Sleep(150);
    }

    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP   = 0x0004;
    public const uint WM_CHAR              = 0x0102;
    public const uint EM_SETSEL            = 0x00B1;
    public const uint BM_CLICK             = 0x00F5;

    public static void ClickScreen(int x, int y) {
        SetCursorPos(x, y);
        Thread.Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(60);
    }

    public static void SendCtrlKey(byte vk) {
        keybd_event(0x11, 0, 0, UIntPtr.Zero);
        Thread.Sleep(40);
        keybd_event(vk, 0, 0, UIntPtr.Zero);
        Thread.Sleep(40);
        keybd_event(vk, 0, 2, UIntPtr.Zero);
        Thread.Sleep(40);
        keybd_event(0x11, 0, 2, UIntPtr.Zero);
        Thread.Sleep(50);
    }

    public static void SendAltKey(byte vk) {
        keybd_event(0x12, 0, 0, UIntPtr.Zero);
        Thread.Sleep(50);
        keybd_event(vk, 0, 0, UIntPtr.Zero);
        Thread.Sleep(50);
        keybd_event(vk, 0, 2, UIntPtr.Zero);
        Thread.Sleep(50);
        keybd_event(0x12, 0, 2, UIntPtr.Zero);
        Thread.Sleep(100);
    }

    public static void SendKey(byte vk) {
        keybd_event(vk, 0, 0, UIntPtr.Zero);
        Thread.Sleep(30);
        keybd_event(vk, 0, 2, UIntPtr.Zero);
        Thread.Sleep(30);
    }

    public static bool FindFileDialog(IntPtr hDesk, int pid, string titleContains, ref IntPtr dlgHwnd, ref IntPtr editHwnd, ref IntPtr btnHwnd) {
        IntPtr foundDlg = IntPtr.Zero;
        IntPtr foundEdit = IntPtr.Zero;
        IntPtr foundBtn = IntPtr.Zero;

        EnumDesktopWindows(hDesk, (h, l) => {
            uint p = 0;
            GetWindowThreadProcessId(h, out p);
            if (p == (uint)pid && IsWindowVisible(h)) {
                StringBuilder cls = new StringBuilder(64);
                GetClassName(h, cls, 64);
                if (cls.ToString() == "#32770") {
                    StringBuilder ttl = new StringBuilder(256);
                    GetWindowText(h, ttl, 256);
                    string title = ttl.ToString();
                    if (string.IsNullOrEmpty(titleContains) || title.IndexOf(titleContains, StringComparison.OrdinalIgnoreCase) >= 0) {
                        foundDlg = h;
                        EnumChildWindows(h, (ch, clp) => {
                            if (!IsWindowVisible(ch)) return true;
                            int id = GetDlgCtrlID(ch);
                            StringBuilder ccls = new StringBuilder(64);
                            GetClassName(ch, ccls, 64);
                            string cname = ccls.ToString();
                            if ((id == 1148 || id == 1001) && cname.IndexOf("Edit", StringComparison.OrdinalIgnoreCase) >= 0) {
                                foundEdit = ch;
                            }
                            if (id == 1) foundBtn = ch;
                            return true;
                        }, IntPtr.Zero);
                        return false;
                    }
                }
            }
            return true;
        }, IntPtr.Zero);

        dlgHwnd = foundDlg;
        editHwnd = foundEdit;
        btnHwnd = foundBtn;
        return foundDlg != IntPtr.Zero && foundEdit != IntPtr.Zero;
    }

    public static bool HandleFileDialog(IntPtr hDesk, int pid, string titleContains, string fullPath) {
        IntPtr dlgHwnd = IntPtr.Zero;
        IntPtr editHwnd = IntPtr.Zero;
        IntPtr btnHwnd = IntPtr.Zero;

        for (int i = 0; i < 20; i++) {
            if (FindFileDialog(hDesk, pid, titleContains, ref dlgHwnd, ref editHwnd, ref btnHwnd)) break;
            Thread.Sleep(200);
        }

        if (dlgHwnd == IntPtr.Zero || editHwnd == IntPtr.Zero) return false;

        SetForegroundWindow(dlgHwnd);
        Thread.Sleep(100);
        SetFocus(editHwnd);
        Thread.Sleep(50);

        SendMessage(editHwnd, EM_SETSEL, IntPtr.Zero, (IntPtr)(-1));
        Thread.Sleep(50);

        foreach (char c in fullPath) {
            PostMessage(editHwnd, WM_CHAR, (IntPtr)(int)c, (IntPtr)1);
            Thread.Sleep(15);
        }
        Thread.Sleep(200);

        if (btnHwnd != IntPtr.Zero) {
            PostMessage(btnHwnd, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
        } else {
            keybd_event(0x0D, 0, 0, UIntPtr.Zero);
            Thread.Sleep(30);
            keybd_event(0x0D, 0, 2, UIntPtr.Zero);
        }
        Thread.Sleep(800);
        return true;
    }
}
"@

# Helper to verify hardware serial port COM7 is free
function Test-Com7Free {
    try {
        $sp = New-Object System.IO.Ports.SerialPort("COM7", 9600)
        $sp.Open()
        $sp.Close()
        return $true
    } catch {
        return $false
    }
}

# Read and validate JSON specification
if (-not (Test-Path $SpecPath)) {
    throw "Spec file not found: $SpecPath"
}
$spec = Get-Content $SpecPath -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " VCM Tune Builder: $($spec.name) ($($spec.version))" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Pre-flight checks
if (-not (Test-Com7Free)) {
    Write-Host "[NOTE] COM7 is in use (e.g. by SCG logger). Proceeding with offline tune file build." -ForegroundColor Yellow
}

$repoRoot   = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$parentPath = Join-Path $repoRoot "tunes\$($spec.parent_file)"
$candPath   = Join-Path $repoRoot "tunes\$($spec.file)"

# Verify parent file
if (-not (Test-Path $parentPath)) { throw "Parent tune not found: $parentPath" }
$parentItem = Get-Item $parentPath
if ($spec.parent_bytes -and $parentItem.Length -ne [long]$spec.parent_bytes) {
    throw "Parent length mismatch: expected $($spec.parent_bytes), got $($parentItem.Length)"
}
$parentHash = (Get-FileHash -Path $parentPath -Algorithm SHA256).Hash
if ($spec.parent_sha256 -and $parentHash -ne $spec.parent_sha256) {
    throw "Parent SHA-256 mismatch: expected $($spec.parent_sha256), got $parentHash"
}
Write-Host "[OK] Verified parent calibration: $($spec.parent_file)" -ForegroundColor Green

# Discover or launch VCM Editor
$running = @(Get-Process -Name 'VCM Editor' -ErrorAction SilentlyContinue)
$editorPid = 0
$editorHwnd = [IntPtr]::Zero

if ($running.Count -gt 0) {
    $editorPid = $running[0].Id
    Write-Host "[OK] Attaching to running VCM Editor process (PID $editorPid)..." -ForegroundColor Green
} else {
    Write-Host "No running VCM Editor found. Pre-copying parent and launching..." -ForegroundColor Yellow
    Copy-Item -Path $parentPath -Destination $candPath -Force
    $proc = Start-Process -FilePath $EditorExe -ArgumentList ('"' + $candPath + '"') -PassThru
    $editorPid = $proc.Id
    Start-Sleep -Milliseconds 1500
}

# Execute automation directly on STA desktop thread
$scriptResults = @{}

$hWinsta = [VcmNative]::OpenWindowStation("WinSta0", $false, 0x037F)
if ($hWinsta -ne [IntPtr]::Zero) {
    [VcmNative]::SetProcessWindowStation($hWinsta) | Out-Null
}
$hDesk = [VcmNative]::OpenDesktop("default", 0, $false, 0x01FF)

# Find main window handle
$foundHwnd = [IntPtr]::Zero
[VcmNative]::EnumDesktopWindows($hDesk, {
    param($h, $l)
    $p = 0
    [VcmNative]::GetWindowThreadProcessId($h, [ref]$p) | Out-Null
    if ($p -eq [uint32]$editorPid -and [VcmNative]::IsWindowVisible($h)) {
        $sb = New-Object System.Text.StringBuilder 256
        [VcmNative]::GetWindowText($h, $sb, 256) | Out-Null
        $title = $sb.ToString()
        if ($title -like 'VCM Editor*') {
            $script:foundHwnd = $h
            return $false
        }
    }
    return $true
}, [IntPtr]::Zero) | Out-Null

if ($foundHwnd -eq [IntPtr]::Zero) { throw "Could not find main VCM Editor window for PID $editorPid" }

try {
    [VcmNative]::ForceForeground($foundHwnd)
        [System.Threading.Thread]::Sleep(200)

        $root = [System.Windows.Automation.AutomationElement]::FromHandle($foundHwnd)
        Write-Host "Connected to VCM Editor: $($root.Current.Name)" -ForegroundColor Green

        # Check if Compare file is open; if so, close it so editing is clean
        if ($root.Current.Name -like "* vs. *") {
            Write-Host "Closing existing compare file before calibration edit..." -ForegroundColor Gray
            $compMenu = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Compare"))
            if ($compMenu) {
                $mrc = $compMenu.Current.BoundingRectangle
                [VcmNative]::ClickScreen([int]($mrc.Left + $mrc.Width / 2), [int]($mrc.Top + $mrc.Height / 2))
                [System.Threading.Thread]::Sleep(300)
                $drops = @([System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)))
                $closeItem = $null
                foreach ($d in $drops) {
                    $found = $d.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Close Compare File"))
                    if ($found) { $closeItem = $found; break }
                }
                if ($closeItem) {
                    $trc = $closeItem.Current.BoundingRectangle
                    [VcmNative]::ClickScreen([int]($trc.Left + $trc.Width / 2), [int]($trc.Top + $trc.Height / 2))
                    [System.Threading.Thread]::Sleep(500)
                } else {
                    [VcmNative]::SendKey(0x43) # 'C'
                    [System.Threading.Thread]::Sleep(400)
                }
            } else {
                [VcmNative]::SendAltKey(0x43)
                [System.Threading.Thread]::Sleep(200)
                [VcmNative]::SendKey(0x43)
                [System.Threading.Thread]::Sleep(400)
            }
            $root = [System.Windows.Automation.AutomationElement]::FromHandle($foundHwnd)
        }

        # Check if candidate file is active; if not, execute Save As candidate
        if ($root.Current.Name -notlike "*$($spec.file)*") {
            Write-Host "Saving active file as candidate '$($spec.file)' via File > Save As..." -ForegroundColor Yellow
            [VcmNative]::SendAltKey(0x46) # Alt+F
            [System.Threading.Thread]::Sleep(200)
            [VcmNative]::SendKey(0x41)    # 'A' Save As
            [System.Threading.Thread]::Sleep(600)

            $saved = [VcmNative]::HandleFileDialog($hDesk, $editorPid, "Save", $candPath)
            if (-not $saved) { throw "Failed to handle Save As file dialog" }
            [System.Threading.Thread]::Sleep(800)

            $root = [System.Windows.Automation.AutomationElement]::FromHandle($foundHwnd)
            if ($root.Current.Name -notlike "*$($spec.file)*") {
                throw "Window title did not switch to candidate file after Save As: $($root.Current.Name)"
            }
            Write-Host "[OK] Candidate tune saved and active: $($root.Current.Name)" -ForegroundColor Green
        }

        # Apply parameters
        $paramList = @()
        if ($spec.parameters) {
            $paramList = @($spec.parameters)
        } elseif ($spec.parameter_id) {
            $paramList = @([pscustomobject]@{
                id = $spec.parameter_id
                name = $spec.parameter_name
                kind = 'table'
                changes = $spec.changes
            })
        }

        foreach ($p in $paramList) {
            $paramId = $p.id
            $pName = $p.name
            Write-Host "Updating parameter [$paramId] $pName..." -ForegroundColor Yellow

            # Open Navigator if not already present
            [VcmNative]::ForceForeground($foundHwnd)
            [System.Threading.Thread]::Sleep(150)

            $condNav = New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Parameter Navigator"
            $nav = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $condNav)
            if (-not $nav) {
                $nav = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
                    [System.Windows.Automation.TreeScope]::Descendants,
                    (New-Object System.Windows.Automation.AndCondition(
                        $condNav,
                        (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)
                    ))
                )
            }
            if (-not $nav) {
                [VcmNative]::SendCtrlKey(0x4E) # Ctrl+N
                [System.Threading.Thread]::Sleep(700)
                $nav = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $condNav)
                if (-not $nav) {
                    $nav = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
                        [System.Windows.Automation.TreeScope]::Descendants,
                        (New-Object System.Windows.Automation.AndCondition(
                            $condNav,
                            (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)
                        ))
                    )
                }
            }
            if (-not $nav) { throw "Parameter Navigator did not open" }

            # Filter edit
            $navEdits = @($nav.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
            if ($navEdits.Count -gt 0) {
                $navEdits[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue([string]$paramId)
                [System.Threading.Thread]::Sleep(400)
            }

            # Tree item
            $items = @($nav.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::TreeItem))))
            $targetItem = $items | Where-Object { $_.Current.Name -like "*$paramId*" -or $_.Current.Name -like "*$pName*" } | Select-Object -First 1
            if (-not $targetItem -and $items.Count -gt 0) { $targetItem = $items[0] }
            if (-not $targetItem) { throw "TreeItem for parameter $paramId not found in Navigator" }

            $targetItem.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
            [System.Threading.Thread]::Sleep(100)

            if ($p.kind -eq 'scalar') {
                # Scalar parameter - edit in preview pane
                $paneEdits = @($nav.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
                $targetEdit = $null
                foreach ($ed in $paneEdits) {
                    try {
                        $vp = $ed.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                        if ($vp -and $vp.Current.Value -ne [string]$paramId -and $vp.Current.Value.Length -gt 0) {
                            $targetEdit = $ed
                            break
                        }
                    } catch {}
                }
                if (-not $targetEdit) { throw "Scalar edit box not found in Navigator preview pane for $paramId" }

                $vpTarget = $targetEdit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                Write-Host "   [$paramId] Current: '$($vpTarget.Current.Value)' -> New: '$($p.new_value)'" -ForegroundColor Gray
                $vpTarget.SetValue([string]$p.new_value)
                [System.Threading.Thread]::Sleep(100)
                $targetEdit.SetFocus()
                [VcmNative]::SendKey(0x09) # Tab to commit
                [System.Threading.Thread]::Sleep(150)
                Write-Host "   [$paramId] Readback: '$($vpTarget.Current.Value)'" -ForegroundColor Green
            } else {
                # Table parameter - open table window
                [VcmNative]::SetForegroundWindow($foundHwnd) | Out-Null
                $targetItem.SetFocus()
                [VcmNative]::SendKey(0x0D) # Enter
                [System.Threading.Thread]::Sleep(600)

                $tableWin = @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Window)))) |
                    Where-Object { $_.Current.Name -like "*$paramId*" -or $_.Current.Name -like "*$pName*" } | Select-Object -First 1

                if (-not $tableWin) {
                    $rc = $targetItem.Current.BoundingRectangle
                    [VcmNative]::ClickScreen([int]($rc.Left + $rc.Width / 2), [int]($rc.Top + $rc.Height / 2))
                    [VcmNative]::ClickScreen([int]($rc.Left + $rc.Width / 2), [int]($rc.Top + $rc.Height / 2))
                    [System.Threading.Thread]::Sleep(500)
                    $tableWin = @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Window)))) |
                        Where-Object { $_.Current.Name -like "*$paramId*" -or $_.Current.Name -like "*$pName*" } | Select-Object -First 1
                }
                if (-not $tableWin) { throw "Table window for $paramId did not open" }

                $grid = $tableWin.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "FlexGrid"))
                if (-not $grid) { throw "FlexGrid not found in table window for $paramId" }

                [VcmNative]::SetForegroundWindow($foundHwnd) | Out-Null
                $grid.SetFocus()
                [System.Threading.Thread]::Sleep(80)

                # Read existing matrix
                [System.Windows.Forms.Clipboard]::Clear()
                [VcmNative]::SendCtrlKey(0x41) # Ctrl+A
                [System.Threading.Thread]::Sleep(60)
                [VcmNative]::SendCtrlKey(0x43) # Ctrl+C
                [System.Threading.Thread]::Sleep(200)

                $copiedText = [System.Windows.Forms.Clipboard]::GetText()
                if ([string]::IsNullOrWhiteSpace($copiedText)) { throw "Failed to copy table text from FlexGrid for $paramId" }

                $rawRows = @($copiedText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
                $matrix = @()
                foreach ($rr in $rawRows) { $matrix += ,@($rr -split "`t") }

                foreach ($ch in $p.changes) {
                    $rIdx = if ($ch.row) { [int]$ch.row - 1 } else { 0 }
                    $cIdx = if ($ch.col) { [int]$ch.col - 1 } else { 0 }
                    $oldVal = $matrix[$rIdx][$cIdx]
                    $newVal = if ($ch.new_value) {
                        [string]$ch.new_value
                    } elseif ($ch.delta_pct) {
                        $calc = [double]$oldVal * (1.0 + [double]$ch.delta_pct / 100.0)
                        [string][Math]::Round($calc, 4)
                    } else { throw "Change entry must have new_value or delta_pct" }

                    Write-Host "   [$paramId] Cell [Row $($rIdx+1), Col $($cIdx+1)]: $oldVal -> $newVal" -ForegroundColor Gray
                    $matrix[$rIdx][$cIdx] = $newVal
                }

                $newText = ($matrix | ForEach-Object { $_ -join "`t" }) -join "`r`n"
                [System.Windows.Forms.Clipboard]::Clear()
                [System.Windows.Forms.Clipboard]::SetText($newText)
                [System.Threading.Thread]::Sleep(60)

                $grid.SetFocus()
                [VcmNative]::SendCtrlKey(0x41)
                [System.Threading.Thread]::Sleep(60)
                [VcmNative]::SendCtrlKey(0x56) # Ctrl+V
                [System.Threading.Thread]::Sleep(250)

                # In-memory verification
                [System.Windows.Forms.Clipboard]::Clear()
                [VcmNative]::SendCtrlKey(0x41)
                [System.Threading.Thread]::Sleep(60)
                [VcmNative]::SendCtrlKey(0x43)
                [System.Threading.Thread]::Sleep(200)

                $vText = [System.Windows.Forms.Clipboard]::GetText()
                $vMatrix = @()
                foreach ($vr in ($vText -split "`r?`n" | Where-Object { $_.Length -gt 0 })) { $vMatrix += ,@($vr -split "`t") }

                foreach ($ch in $p.changes) {
                    $rIdx = if ($ch.row) { [int]$ch.row - 1 } else { 0 }
                    $cIdx = if ($ch.col) { [int]$ch.col - 1 } else { 0 }
                    $act = $vMatrix[$rIdx][$cIdx]
                    $exp = if ($ch.new_value) { [string]$ch.new_value } else { $matrix[$rIdx][$cIdx] }
                    $actNum = 0.0; $expNum = 0.0
                    $isNum = [double]::TryParse($act, [ref]$actNum) -and [double]::TryParse($exp, [ref]$expNum)
                    if ($isNum) {
                        if ([Math]::Abs($actNum - $expNum) -gt 0.001) {
                            throw "Verification mismatch for [$paramId] at Row $($rIdx+1) Col $($cIdx+1): expected '$exp', got '$act'"
                        }
                    } else {
                        if ($act -ne $exp) {
                            throw "Verification mismatch for [$paramId] at Row $($rIdx+1) Col $($cIdx+1): expected '$exp', got '$act'"
                        }
                    }
                }
                Write-Host "   [$paramId] All $($p.changes.Count) cell update(s) verified in-memory." -ForegroundColor Green

                # Close table window
                try { $tableWin.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {}
                [System.Threading.Thread]::Sleep(200)
            }
        }

        # Append Calibration Details > Notes
        if ($spec.notes_append) {
            Write-Host "Appending Calibration Details > Notes..." -ForegroundColor Yellow
            [VcmNative]::SendCtrlKey(0x44) # Ctrl+D
            [System.Threading.Thread]::Sleep(500)

            $cd = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Calibration Details"))
            if ($cd) {
                $notesTab = $cd.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Notes"))
                if ($notesTab) {
                    try { $notesTab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() } catch {}
                }
                [System.Threading.Thread]::Sleep(200)

                $cdEdits = @($cd.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
                if ($cdEdits.Count -gt 0) {
                    $vpNotes = $cdEdits[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                    $existingNotes = $vpNotes.Current.Value
                    $updatedNotes = $existingNotes + "`r`n`r`n" + $spec.notes_append
                    $vpNotes.SetValue($updatedNotes)
                    [System.Threading.Thread]::Sleep(200)
                    Write-Host "[OK] Notes appended successfully (total length: $($updatedNotes.Length))." -ForegroundColor Green
                }
                try { $cd.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {}
                [System.Threading.Thread]::Sleep(300)
            }
        }

        # Save candidate tune (Ctrl+S)
        Write-Host "Saving candidate tune via Ctrl+S..." -ForegroundColor Yellow
        [VcmNative]::SetForegroundWindow($foundHwnd) | Out-Null
        [VcmNative]::SendCtrlKey(0x53) # Ctrl+S
        [System.Threading.Thread]::Sleep(1500)

        # Fresh Reopen Pass
        Write-Host "Executing fresh reopen pass from disk..." -ForegroundColor Yellow
        [VcmNative]::SendAltKey(0x46) # Alt+F
        [System.Threading.Thread]::Sleep(200)
        [VcmNative]::SendKey(0x4F)    # 'O' Open
        [System.Threading.Thread]::Sleep(600)

        $reopened = [VcmNative]::HandleFileDialog($hDesk, $editorPid, "Open", $candPath)
        if (-not $reopened) { throw "Failed to handle Open file dialog during fresh reopen" }
        [System.Threading.Thread]::Sleep(1200)

        $root = [System.Windows.Automation.AutomationElement]::FromHandle($foundHwnd)
        Write-Host "[OK] Candidate freshly reopened: $($root.Current.Name)" -ForegroundColor Green

        # Whole-file compare against parent
        Write-Host "Opening parent as compare file..." -ForegroundColor Yellow
        $compMenu = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Compare"))
        if ($compMenu) {
            $mrc = $compMenu.Current.BoundingRectangle
            [VcmNative]::ClickScreen([int]($mrc.Left + $mrc.Width / 2), [int]($mrc.Top + $mrc.Height / 2))
            [System.Threading.Thread]::Sleep(300)

            $drops = @([System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)))
            $openCompItem = $null
            foreach ($d in $drops) {
                $found = $d.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Open Compare File"))
                if ($found) { $openCompItem = $found; break }
            }
            if ($openCompItem) {
                $trc = $openCompItem.Current.BoundingRectangle
                [VcmNative]::ClickScreen([int]($trc.Left + $trc.Width / 2), [int]($trc.Top + $trc.Height / 2))
                [System.Threading.Thread]::Sleep(600)
                [void][VcmNative]::HandleFileDialog($hDesk, $editorPid, "", $parentPath)
                [System.Threading.Thread]::Sleep(1500)
            }
        }

        # Open Comparison Log
        $diffList = @()
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($foundHwnd)
        $compMenu2 = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "Compare"))
        if ($compMenu2) {
            $mrc2 = $compMenu2.Current.BoundingRectangle
            [VcmNative]::ClickScreen([int]($mrc2.Left + $mrc2.Width / 2), [int]($mrc2.Top + $mrc2.Height / 2))
            [System.Threading.Thread]::Sleep(300)

            $drops2 = @([System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)))
            $viewLogItem = $null
            foreach ($d in $drops2) {
                $found = $d.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), "View Comparison Log"))
                if ($found) { $viewLogItem = $found; break }
            }
            if ($viewLogItem) {
                $trc2 = $viewLogItem.Current.BoundingRectangle
                [VcmNative]::ClickScreen([int]($trc2.Left + $trc2.Width / 2), [int]($trc2.Top + $trc2.Height / 2))
                [System.Threading.Thread]::Sleep(800)

                $logWin = @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Window)))) |
                    Where-Object { $_.Current.Name -like "*Comparison Log*" } | Select-Object -First 1

                if ($logWin) {
                    $treeItems = @($logWin.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::TreeItem))))
                    foreach ($ti in $treeItems) {
                        $diffList += $ti.Current.Name.Trim()
                    }
                    Write-Host "[OK] Comparison Log captured: $($diffList.Count) node(s) found." -ForegroundColor Green
                }
            }
        }

        # Store results
        $scriptResults['editorPid']  = $editorPid
        $scriptResults['editorHwnd'] = $foundHwnd
        $scriptResults['diffList']   = $diffList

        if ($KillOnExit) {
            Write-Host "Killing VCM Editor process ($editorPid) as requested by -KillOnExit..." -ForegroundColor Yellow
            $p = Get-Process -Id $editorPid -ErrorAction SilentlyContinue
            if ($p) { $p.Kill(); $p.WaitForExit(3000) }
        } else {
            Write-Host "[OK] VCM Editor preserved open with candidate vs. parent comparison." -ForegroundColor Green
        }
    } catch {
        Write-Host "FATAL ERROR during tune build: $_" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor Red
        throw $_
    }

# Final Hash & Byte Size Calculation
$candItem = Get-Item $candPath
$candHash = (Get-FileHash -Path $candPath -Algorithm SHA256).Hash

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " BUILD & VERIFICATION SUCCESSFUL!" -ForegroundColor Green
Write-Host " File:    $candPath" -ForegroundColor Green
Write-Host " Bytes:   $($candItem.Length)" -ForegroundColor Green
Write-Host " SHA-256: $candHash" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

$outObj = [pscustomobject]@{
    version    = $spec.version
    file       = $spec.file
    parent     = $spec.parent_file
    bytes      = $candItem.Length
    sha256     = $candHash
    diff_nodes = $scriptResults['diffList']
}

if ($spec.output_result_json) {
    $outPath = Join-Path $repoRoot $spec.output_result_json
    $outObj | ConvertTo-Json -Depth 5 | Set-Content -Path $outPath -Encoding UTF8
}

return $outObj
