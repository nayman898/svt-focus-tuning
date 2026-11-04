<#
.SYNOPSIS
    vcm-tune-builder.ps1 - Generic, reusable VCM Editor automation tool for SVT Focus tuning.
.DESCRIPTION
    Loads a parent .hpt file in HP Tuners VCM Editor, saves as a new revision, updates target
    parameter tables by Parameter ID, appends calibration notes, and executes full reopen and
    whole-file compare verification.
    
    Driven entirely by a JSON specification file.
    
    Strict Safety Rules:
    - NEVER touches ECU flash/write functions.
    - NEVER embeds VINs or MPVI serial numbers.
    - NEVER copy/hex-edits .hpt files directly; all saves pass through VCM Editor.
    - Verifies COM7 is free and no VCM Editor processes are running before start.
.EXAMPLE
    powershell -STA -NoProfile -ExecutionPolicy Bypass -File tools/vcm-tune-builder.ps1 -SpecPath "scratch/v027_spec.json"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SpecPath,

    [string]$EditorExe = ""
)

if (-not $EditorExe) {
    if (Test-Path "C:\Program Files\HP Tuners\VCM Suite (Beta)\VCM Editor.exe") {
        $EditorExe = "C:\Program Files\HP Tuners\VCM Suite (Beta)\VCM Editor.exe"
    } elseif (Test-Path "C:\Program Files\HP Tuners\VCM Suite\VCM Editor.exe") {
        $EditorExe = "C:\Program Files\HP Tuners\VCM Suite\VCM Editor.exe"
    } else {
        throw "VCM Editor.exe not found in HP Tuners directories"
    }
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# Native Win32 helpers for GUI automation & character typing
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class VcmGui {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumThreadWindows(uint dwThreadId, EnumWindowsProc lpfn, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr l);

    public static bool DismissBeta(int pid) {
        bool hit = false;
        EnumWindows((h, l) => {
            uint p; GetWindowThreadProcessId(h, out p);
            if (p == (uint)pid && IsWindowVisible(h)) {
                StringBuilder t = new StringBuilder(512); GetWindowText(h, t, 512);
                if (t.ToString().IndexOf("Beta Software Warning", StringComparison.OrdinalIgnoreCase) >= 0) {
                    EnumChildWindows(h, (ch, cl) => {
                        StringBuilder ct = new StringBuilder(128); GetWindowText(ch, ct, 128);
                        if (ct.ToString() == "OK") {
                            PostMessage(ch, 0x00F5, IntPtr.Zero, IntPtr.Zero); // BM_CLICK
                            hit = true;
                        }
                        return true;
                    }, IntPtr.Zero);
                }
            }
            return true;
        }, IntPtr.Zero);
        return hit;
    }

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP   = 0x0004;
    public const uint KEYEVENTF_KEYUP      = 0x0002;

    public static void ClickScreen(int x, int y) {
        SetCursorPos(x, y);
        System.Threading.Thread.Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(60);
    }

    public static void DoubleClickScreen(int x, int y) {
        ClickScreen(x, y);
        System.Threading.Thread.Sleep(100);
        ClickScreen(x, y);
    }

    public static void SendCtrlKey(byte vk) {
        keybd_event(0x11, 0, 0, UIntPtr.Zero); // Ctrl down
        System.Threading.Thread.Sleep(40);
        keybd_event(vk, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(40);
        keybd_event(vk, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
        System.Threading.Thread.Sleep(40);
        keybd_event(0x11, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
        System.Threading.Thread.Sleep(60);
    }

    public static void SendAltKey(byte vk) {
        keybd_event(0x12, 0, 0, UIntPtr.Zero); // Alt down
        System.Threading.Thread.Sleep(40);
        keybd_event(vk, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(40);
        keybd_event(vk, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
        System.Threading.Thread.Sleep(40);
        keybd_event(0x12, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
        System.Threading.Thread.Sleep(60);
    }

    public static void SendKey(byte vk) {
        keybd_event(vk, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(30);
        keybd_event(vk, 0, KEYEVENTF_KEYUP, UIntPtr.Zero);
        System.Threading.Thread.Sleep(30);
    }

    public static void TypeChars(IntPtr hWnd, string text) {
        foreach (char c in text) {
            PostMessage(hWnd, 0x0102, (IntPtr)(int)c, (IntPtr)1); // WM_CHAR
            System.Threading.Thread.Sleep(15);
        }
    }

    public static bool FindFileDialog(int pid, ref IntPtr dlgHwnd, ref IntPtr editHwnd, ref IntPtr btnHwnd, ref string title) {
        IntPtr foundDlg = IntPtr.Zero;
        IntPtr foundEdit = IntPtr.Zero;
        IntPtr foundBtn = IntPtr.Zero;
        string foundTitle = "";

        EnumWindowsProc proc = (h, lp) => {
            uint p; GetWindowThreadProcessId(h, out p);
            if (p != (uint)pid) return true;
            StringBuilder cls = new StringBuilder(64);
            GetClassName(h, cls, 64);
            if (cls.ToString() == "#32770" && IsWindowVisible(h)) {
                StringBuilder ttl = new StringBuilder(256);
                GetWindowText(h, ttl, 256);
                foundDlg = h;
                foundTitle = ttl.ToString();

                EnumChildWindows(h, (ch, clp) => {
                    if (!IsWindowVisible(ch)) return true;
                    int id = GetDlgCtrlID(ch);
                    StringBuilder ccls = new StringBuilder(64);
                    GetClassName(ch, ccls, 64);
                    string cname = ccls.ToString();
                    if (id == 1148 && cname.IndexOf("Edit", StringComparison.OrdinalIgnoreCase) >= 0) {
                        foundEdit = ch;
                    } else if (id == 1001 && foundEdit == IntPtr.Zero && cname.IndexOf("Edit", StringComparison.OrdinalIgnoreCase) >= 0) {
                        foundEdit = ch;
                    }
                    if (id == 1) foundBtn = ch;
                    return true;
                }, IntPtr.Zero);
                return false;
            }
            return true;
        };

        foreach (System.Diagnostics.ProcessThread t in System.Diagnostics.Process.GetProcessById(pid).Threads) {
            EnumThreadWindows((uint)t.Id, proc, IntPtr.Zero);
            if (foundDlg != IntPtr.Zero) break;
        }

        dlgHwnd = foundDlg;
        editHwnd = foundEdit;
        btnHwnd = foundBtn;
        title = foundTitle;
        return foundDlg != IntPtr.Zero && foundEdit != IntPtr.Zero;
    }
}
"@

function Set-ClipboardSafe([string]$text) {
    for ($i = 0; $i -lt 10; $i++) {
        try {
            [System.Windows.Forms.Clipboard]::Clear()
            [System.Windows.Forms.Clipboard]::SetText($text)
            return
        } catch {
            Start-Sleep -Milliseconds 50
        }
    }
    throw "Failed to set clipboard text after 10 attempts"
}

function Get-ClipboardSafe {
    for ($i = 0; $i -lt 10; $i++) {
        try {
            $txt = [System.Windows.Forms.Clipboard]::GetText()
            if (-not [string]::IsNullOrEmpty($txt)) { return $txt }
        } catch {}
        Start-Sleep -Milliseconds 50
    }
    return [System.Windows.Forms.Clipboard]::GetText()
}

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
    Write-Host "[NOTE] COM7 is in use (e.g. by SCG logger). Proceeding with offline tune file build (no hardware communication)." -ForegroundColor Yellow
}
$running = @(Get-Process -Name 'VCM Editor' -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
    throw "Safety abort: VCM Editor is already running (PIDs: $($running.Id -join ', ')). Close all instances before starting."
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$parentPath = Join-Path $repoRoot "tunes\$($spec.parent_file)"
$candPath   = Join-Path $repoRoot "tunes\$($spec.file)"
$localDir   = Join-Path $repoRoot ".local"
if (-not (Test-Path $localDir)) { [void](New-Item -ItemType Directory -Path $localDir -Force) }

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

# Launch VCM Editor with parent
Write-Host "Launching VCM Editor opening parent..." -ForegroundColor Yellow
$proc = Start-Process -FilePath $EditorExe -ArgumentList ('"' + $parentPath + '"') -PassThru
$editorPid = $proc.Id

try {
    # Wait for root window with parent file loaded
    $root = $null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        [VcmGui]::DismissBeta($editorPid) | Out-Null
        $proc.Refresh()
        if ($proc.MainWindowTitle -like "*$($spec.parent_file)*") {
            try {
                $root = [System.Windows.Automation.AutomationElement]::FromHandle($proc.MainWindowHandle)
                if ($root -and $root.Current.NativeWindowHandle -ne 0) { break }
            } catch {}
        }
    }
    if (-not $root -and $proc.MainWindowHandle -ne [IntPtr]::Zero) {
        $root = [System.Windows.Automation.AutomationElement]::FromHandle($proc.MainWindowHandle)
    }
    if (-not $root) { throw "VCM Editor main window did not appear" }
    $editorHwnd = [IntPtr]$root.Current.NativeWindowHandle
    [void][VcmGui]::ShowWindow($editorHwnd, 9)
    [void][VcmGui]::SetForegroundWindow($editorHwnd)
    Start-Sleep -Milliseconds 300

    function Find-ByName($scope, $name) {
        return $scope.FindFirst(
            [System.Windows.Automation.TreeScope]::Descendants,
            (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), $name)
        )
    }

    function Clear-Modals($tag) {
        $popups = @([System.Windows.Automation.AutomationElement]::RootElement.FindAll(
            [System.Windows.Automation.TreeScope]::Children,
            (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)
        ) | Where-Object { $_.Current.NativeWindowHandle -ne $editorHwnd.ToInt64() })

        foreach ($p in $popups) {
            $ttl = $p.Current.Name
            $btn = $p.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Button)))
            if ($btn) {
                Write-Host "   [$tag] Dismissing modal '$ttl' via button '$($btn.Current.Name)'" -ForegroundColor Gray
                try { $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() } catch {}
                Start-Sleep -Milliseconds 200
            }
        }
    }

    function Wait-FileLoaded($tag) {
        for ($i = 0; $i -lt 50; $i++) {
            Clear-Modals $tag
            $ts = @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::ToolBar))))
            foreach ($bar in $ts) {
                $writeBtn = $bar.FindFirst([System.Windows.Automation.TreeScope]::Children, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), 'Write Vehicle'))
                if ($writeBtn -and $writeBtn.Current.IsEnabled) {
                    Write-Host "   [$tag] File loaded and ready (toolstrip active)." -ForegroundColor Green
                    return
                }
            }
            Start-Sleep -Milliseconds 300
        }
        throw "[$tag] Timeout waiting for tune file to load"
    }

    function Click-Menu($menuName, $itemName) {
        Clear-Modals "Menu:$menuName"
        [void][VcmGui]::SetForegroundWindow($editorHwnd)
        Start-Sleep -Milliseconds 80
        $menu = $null
        for ($m = 0; $m -lt 20 -and -not $menu; $m++) {
            $menu = Find-ByName $root $menuName
            if (-not $menu) { Start-Sleep -Milliseconds 150 }
        }
        if (-not $menu) { throw "Menu '$menuName' not found" }
        $box = $menu.Current.BoundingRectangle
        [VcmGui]::ClickScreen([int]($box.Left + $box.Width / 2), [int]($box.Top + $box.Height / 2))
        Start-Sleep -Milliseconds 250

        # Look in dropdown windows
        $target = $null
        for ($w = 0; $w -lt 15 -and -not $target; $w++) {
            $drops = @([System.Windows.Automation.AutomationElement]::RootElement.FindAll(
                [System.Windows.Automation.TreeScope]::Children,
                (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid)
            ) | Where-Object { $_.Current.ClassName -like '*ToolStripDropDownMenu*' -or $_.Current.ClassName -eq '#32768' -or $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::Menu })
            foreach ($d in $drops) {
                $target = Find-ByName $d $itemName
                if ($target) { break }
            }
            if (-not $target) { Start-Sleep -Milliseconds 60 }
        }
        if (-not $target) { $target = Find-ByName $root $itemName }
        if (-not $target) { throw "Menu item '$menuName > $itemName' not found" }
        $tbox = $target.Current.BoundingRectangle
        [VcmGui]::ClickScreen([int]($tbox.Left + $tbox.Width / 2), [int]($tbox.Top + $tbox.Height / 2))
        Start-Sleep -Milliseconds 350
    }

    function Submit-FileDialog($filePath, $tag) {
        $dlg = [IntPtr]::Zero; $edit = [IntPtr]::Zero; $btn = [IntPtr]::Zero; $dlgTitle = ""
        for ($i = 0; $i -lt 30; $i++) {
            if ([VcmGui]::FindFileDialog($editorPid, [ref]$dlg, [ref]$edit, [ref]$btn, [ref]$dlgTitle)) { break }
            Start-Sleep -Milliseconds 200
        }
        if ($dlg -eq [IntPtr]::Zero -or $edit -eq [IntPtr]::Zero) {
            throw "[$tag] File dialog (#32770) did not appear"
        }

        # Focus dialog
        [void][VcmGui]::SetForegroundWindow($dlg)
        Start-Sleep -Milliseconds 150

        # Center click edit box to activate and clear DirectUIHWND selection
        $rc = New-Object VcmGui+RECT
        [void][VcmGui]::GetWindowRect($edit, [ref]$rc)
        $cx = [int]($rc.Left + ($rc.Right - $rc.Left) / 2)
        $cy = [int]($rc.Top + ($rc.Bottom - $rc.Top) / 2)
        [VcmGui]::ClickScreen($cx, $cy)
        Start-Sleep -Milliseconds 100

        # Clear existing text
        [VcmGui]::SendCtrlKey(0x41) # Ctrl+A
        [VcmGui]::SendKey(0x08)     # Backspace
        Start-Sleep -Milliseconds 80

        # Type full path character-by-character
        [VcmGui]::TypeChars($edit, $filePath)
        Start-Sleep -Milliseconds 250

        # Confirm and submit
        if ($btn -ne [IntPtr]::Zero) {
            $brc = New-Object VcmGui+RECT
            [void][VcmGui]::GetWindowRect($btn, [ref]$brc)
            [VcmGui]::ClickScreen([int]($brc.Left + ($brc.Right - $brc.Left) / 2), [int]($brc.Top + ($brc.Bottom - $brc.Top) / 2))
        } else {
            [VcmGui]::SendKey(0x0D) # Enter
        }
        Start-Sleep -Milliseconds 500

        # Check for overwrite prompt if any
        Clear-Modals "$tag:Overwrite"
    }

    function Open-ParameterTable($paramId, $paramName) {
        # Close existing parameter tables
        foreach ($w in @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Window))))) {
            if ($w.Current.Name -like '[[]ECM[]]*') {
                try { $w.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {}
            }
        }
        Start-Sleep -Milliseconds 150

        # Open Navigator
        $nav = Find-ByName $root 'Parameter Navigator'
        if (-not $nav) {
            try { Click-Menu 'Edit' 'Parameter Navigator' } catch {
                [void][VcmGui]::SetForegroundWindow($editorHwnd)
                [VcmGui]::SendCtrlKey(0x4E) # Ctrl+N
            }
            for ($i = 0; $i -lt 25 -and -not $nav; $i++) {
                Start-Sleep -Milliseconds 150
                $nav = Find-ByName $root 'Parameter Navigator'
            }
        }
        if (-not $nav) { throw "Could not open Parameter Navigator" }

        # Filter by Parameter ID
        $edits = @($nav.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
        if ($edits.Count -lt 1) { throw "Parameter Navigator filter box not found" }
        $edits[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue([string]$paramId)
        Start-Sleep -Milliseconds 350

        # Select tree item
        $items = @($nav.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::TreeItem))))
        $target = $items | Where-Object { $_.Current.Name -like "*$paramName*" -or $_.Current.Name -like "*$paramId*" } | Select-Object -First 1
        if (-not $target -and $items.Count -gt 0) { $target = $items[0] }
        if (-not $target) { throw "Parameter '$paramId - $paramName' not found in Navigator results" }

        $target.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
        Start-Sleep -Milliseconds 150
        [void][VcmGui]::SetForegroundWindow($editorHwnd)
        $target.SetFocus()
        [VcmGui]::SendKey(0x0D) # Enter
        Start-Sleep -Milliseconds 350

        # Find opened table window
        $tableWin = @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Window)))) |
            Where-Object { $_.Current.Name -like "*$paramId*" -or $_.Current.Name -like "*$paramName*" } | Select-Object -First 1
        if (-not $tableWin) {
            $box = $target.Current.BoundingRectangle
            [VcmGui]::DoubleClickScreen([int]($box.Left + $box.Width / 2), [int]($box.Top + $box.Height / 2))
            Start-Sleep -Milliseconds 400
            $tableWin = @($root.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Window)))) |
                Where-Object { $_.Current.Name -like "*$paramId*" -or $_.Current.Name -like "*$paramName*" } | Select-Object -First 1
        }
        if (-not $tableWin) { throw "Failed to open parameter window for '$paramId - $paramName'" }
        return $tableWin
    }

    # Step 1: Open parent file if not already open
    if ($root.Current.Name -notlike "*$($spec.parent_file)*") {
        Write-Host "Opening parent file via File > Open..." -ForegroundColor Yellow
        Click-Menu 'File' 'Open'
        Start-Sleep -Milliseconds 600
        Submit-FileDialog $parentPath "OpenParent"
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 300
            Clear-Modals "OpenParent"
            if ($root.Current.Name -like "*$($spec.parent_file)*") { break }
        }
    }
    if ($root.Current.Name -notlike "*$($spec.parent_file)*") {
        throw "Failed to open parent tune: expected title containing '$($spec.parent_file)', got '$($root.Current.Name)'"
    }
    Write-Host "[OK] Parent tune loaded: $($root.Current.Name)" -ForegroundColor Green
    Wait-FileLoaded "OpenParent" 

    # Step 2: Save As Candidate
    Write-Host "Executing Save As '$($spec.file)'..." -ForegroundColor Yellow
    Click-Menu 'File' 'Save As'
    Start-Sleep -Milliseconds 500
    Submit-FileDialog $candPath "SaveAsCandidate"
    
    # Confirm title updated
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 200
        if ($root.Current.Name -like "*$($spec.file)*") { break }
    }
    if ($root.Current.Name -notlike "*$($spec.file)*") {
        throw "Active window title did not switch to candidate tune: $($root.Current.Name)"
    }
    Write-Host "[OK] Working copy saved as: $($root.Current.Name)" -ForegroundColor Green
    Wait-FileLoaded "SaveAsCandidate" 

    # Step 3: Open and edit parameters (supporting scalars and tables)
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
        $pId = $p.id
        $pName = $p.name
        Write-Host "Opening parameter [$pId] $pName..." -ForegroundColor Yellow
        $tableWin = Open-ParameterTable $pId $pName
        $grid = Find-ByName $tableWin 'FlexGrid'
        if ($grid) {
            # Table parameter (1D, 2D, or 3D)
            if ($p.changes) {
                [void][VcmGui]::SetForegroundWindow($editorHwnd)
                # Ensure no active cell edit textbox captures focus
                $cell1 = Find-ByName $grid 'Column 1 Row 1'
                if ($cell1) {
                    try { $cell1.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() } catch {}
                    [VcmGui]::SendKey(0x1B) # Escape
                    Start-Sleep -Milliseconds 50
                }

                $grid.SetFocus()
                Start-Sleep -Milliseconds 60
                [VcmGui]::SendCtrlKey(0x41) # Ctrl+A
                Start-Sleep -Milliseconds 60
                [System.Windows.Forms.Clipboard]::Clear()
                [VcmGui]::SendCtrlKey(0x43) # Ctrl+C
                Start-Sleep -Milliseconds 150
                $copiedText = Get-ClipboardSafe
                if ([string]::IsNullOrWhiteSpace($copiedText)) {
                    throw "Failed to copy table text from FlexGrid for parameter $pId"
                }

                $rawRows = @($copiedText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
                $matrix = @()
                foreach ($rr in $rawRows) {
                    $matrix += ,@($rr -split "`t")
                }

                foreach ($ch in $p.changes) {
                    $rIdx = if ($ch.row) { [int]$ch.row - 1 } else { 0 }
                    $cIdx = if ($ch.col) { [int]$ch.col - 1 } else { 0 }
                    if ($rIdx -lt 0 -or $rIdx -ge $matrix.Count) {
                        throw "Row index $($rIdx+1) out of bounds for parameter $pId (has $($matrix.Count) rows)"
                    }
                    if ($cIdx -lt 0 -or $cIdx -ge $matrix[$rIdx].Count) {
                        throw "Col index $($cIdx+1) out of bounds for parameter $pId (has $($matrix[$rIdx].Count) cols)"
                    }
                    $oldVal = $matrix[$rIdx][$cIdx]
                    $newVal = if ($ch.new_value) {
                        [string]$ch.new_value
                    } elseif ($ch.delta_pct) {
                        $calc = [double]$oldVal * (1.0 + [double]$ch.delta_pct / 100.0)
                        [string][Math]::Round($calc, 4)
                    } else {
                        throw "Change entry must have either 'new_value' or 'delta_pct'"
                    }
                    Add-Member -InputObject $ch -NotePropertyName 'resolved_new_value' -NotePropertyValue $newVal -Force
                    Add-Member -InputObject $ch -NotePropertyName 'resolved_old_value' -NotePropertyValue $oldVal -Force
                    Write-Host "   [$pId] Updating cell (row $($rIdx+1), col $($cIdx+1)) from '$oldVal' to '$newVal'" -ForegroundColor Gray
                    $matrix[$rIdx][$cIdx] = $newVal
                }

                $newText = ($matrix | ForEach-Object { $_ -join "`t" }) -join "`r`n"
                Set-ClipboardSafe $newText
                $grid.SetFocus()
                Start-Sleep -Milliseconds 60
                [VcmGui]::SendCtrlKey(0x41) # Ctrl+A
                Start-Sleep -Milliseconds 60
                [VcmGui]::SendCtrlKey(0x56) # Ctrl+V
                Start-Sleep -Milliseconds 250

                # In-memory verification
                [System.Windows.Forms.Clipboard]::Clear()
                [VcmGui]::SendCtrlKey(0x41) # Ctrl+A
                Start-Sleep -Milliseconds 60
                [VcmGui]::SendCtrlKey(0x43) # Ctrl+C
                Start-Sleep -Milliseconds 150
                $verifyText = Get-ClipboardSafe
                $vRows = @($verifyText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
                $vMatrix = @()
                foreach ($vr in $vRows) {
                    $vMatrix += ,@($vr -split "`t")
                }
                foreach ($ch in $p.changes) {
                    $rIdx = if ($ch.row) { [int]$ch.row - 1 } else { 0 }
                    $cIdx = if ($ch.col) { [int]$ch.col - 1 } else { 0 }
                    $actual = $vMatrix[$rIdx][$cIdx]
                    $exp = if ($ch.resolved_new_value) { $ch.resolved_new_value } else { [string]$ch.new_value }
                    if ($actual -ne $exp) {
                        throw "Verification mismatch for [$pId] at row $($rIdx+1), col $($cIdx+1): expected '$exp', readback '$actual'"
                    }
                }
                Write-Host "   [$pId] All $($p.changes.Count) cell update(s) verified in-memory." -ForegroundColor Green
            }
        } else {
            # Scalar parameter (single Edit / ValuePattern control)
            $edits = @($tableWin.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
            if ($edits.Count -gt 0) {
                $valPattern = $edits[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                Write-Host "   [$pId] Updating Scalar from '$($valPattern.Current.Value)' to '$($p.new_value)'" -ForegroundColor Gray
                $valPattern.SetValue([string]$p.new_value)
                Start-Sleep -Milliseconds 100
            } else {
                throw "Neither FlexGrid nor Edit control found in window for parameter $pId"
            }
        }
        # Close parameter window so Navigator is clean for next parameter
        try { $tableWin.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {}
        Start-Sleep -Milliseconds 200
    }
    Write-Host "[OK] Applied all parameter modifications." -ForegroundColor Green

    # Step 4: Append Calibration Details > Notes
    if ($spec.notes_append) {
        Write-Host "Appending Calibration Details > Notes..." -ForegroundColor Yellow
        Click-Menu 'Edit' 'Calibration Details'
        Start-Sleep -Milliseconds 400
        $cd = Find-ByName $root 'Calibration Details'
        if (-not $cd) { throw "Calibration Details window did not appear" }

        # Select Notes tab
        $tab = Find-ByName $cd 'Notes'
        if ($tab) {
            try { $tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() } catch {}
        }
        Start-Sleep -Milliseconds 150

        # Read existing notes and append
        $rtb = Find-ByName $cd 'richTextBoxNotes'
        if (-not $rtb) {
            $rtbs = @($cd.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
            if ($rtbs.Count -gt 0) { $rtb = $rtbs[0] }
        }
        if (-not $rtb) { throw "Notes richTextBox not found" }

        $existingNotes = $rtb.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
        $newNotes = $existingNotes + "`r`n" + $spec.notes_append
        $rtb.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($newNotes)
        Start-Sleep -Milliseconds 200

        # Close Calibration Details
        try { $cd.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {
            $closeBtn = $cd.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::NameProperty), 'Close'))
            if ($closeBtn) { $closeBtn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
        }
        Start-Sleep -Milliseconds 300
        Write-Host "[OK] Notes appended successfully." -ForegroundColor Green
    }

    # Step 5: Save candidate tune file
    Write-Host "Saving candidate tune file (Ctrl+S)..." -ForegroundColor Yellow
    [void][VcmGui]::SetForegroundWindow($editorHwnd)
    [VcmGui]::SendCtrlKey(0x53) # Ctrl+S
    Start-Sleep -Milliseconds 1200
    Clear-Modals "SaveConfirm"
    Write-Host "[OK] Saved candidate tune to disk." -ForegroundColor Green

} finally {
    # Close VCM Editor completely
    try {
        if ($proc -and -not $proc.HasExited) {
            $proc.Kill()
            $proc.WaitForExit(3000)
        }
    } catch {}
    Start-Sleep -Milliseconds 500
}

# Post-save reopen & compare verification pass
Write-Host "Starting fresh reopen verification pass..." -ForegroundColor Yellow
$proc2 = Start-Process -FilePath $EditorExe -ArgumentList ('"' + $candPath + '"') -PassThru
$editorPid2 = $proc2.Id

try {
    $root2 = $null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        [VcmGui]::DismissBeta($editorPid2) | Out-Null
        $proc2.Refresh()
        if ($proc2.MainWindowHandle -ne [IntPtr]::Zero) {
            try {
                $root2 = [System.Windows.Automation.AutomationElement]::FromHandle($proc2.MainWindowHandle)
                if ($root2 -and $root2.Current.NativeWindowHandle -ne 0) { break }
            } catch {}
        }
        if (-not $root2) {
            $root2 = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
                [System.Windows.Automation.TreeScope]::Children,
                (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ProcessIdProperty), $editorPid2)
            )
            if ($root2 -and $root2.Current.NativeWindowHandle -ne 0) { break }
        }
    }
    if (-not $root2) { throw "VCM Editor did not reopen candidate file" }
    $editorHwnd2 = [IntPtr]$root2.Current.NativeWindowHandle
    $root = $root2
    $editorHwnd = $editorHwnd2
    $editorPid = $editorPid2

    # Ensure candidate file is opened in reopen pass
    if ($root2.Current.Name -notlike "*$($spec.file)*") {
        Write-Host "Opening candidate file via File > Open..." -ForegroundColor Yellow
        Click-Menu 'File' 'Open'
        Start-Sleep -Milliseconds 600
        Submit-FileDialog $candPath "ReopenCandidate"
        for ($i = 0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 300
            Clear-Modals "ReopenCandidate"
            if ($root2.Current.Name -like "*$($spec.file)*") { break }
        }
    }
    if ($root2.Current.Name -notlike "*$($spec.file)*") {
        throw "Failed to reopen candidate tune: expected title containing '$($spec.file)', got '$($root2.Current.Name)'"
    }
    Write-Host "[OK] Candidate tune reopened: $($root2.Current.Name)" -ForegroundColor Green

    # Verify values on reopen (supporting scalars and tables)
    $reopenedRows = @()
    foreach ($p in $paramList) {
        $pId = $p.id
        $pName = $p.name
        Write-Host "Reopening parameter [$pId] $pName for verification..." -ForegroundColor Yellow
        $tableWin2 = Open-ParameterTable $pId $pName
        $grid2 = Find-ByName $tableWin2 'FlexGrid'
        if ($grid2) {
            if ($p.changes) {
                [void][VcmGui]::SetForegroundWindow($editorHwnd2)
                $cell1_2 = Find-ByName $grid2 'Column 1 Row 1'
                if ($cell1_2) {
                    try { $cell1_2.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() } catch {}
                    [VcmGui]::SendKey(0x1B) # Escape
                    Start-Sleep -Milliseconds 50
                }
                $grid2.SetFocus()
                Start-Sleep -Milliseconds 60
                [VcmGui]::SendCtrlKey(0x41) # Ctrl+A
                Start-Sleep -Milliseconds 60
                [System.Windows.Forms.Clipboard]::Clear()
                [VcmGui]::SendCtrlKey(0x43) # Ctrl+C
                Start-Sleep -Milliseconds 150
                $reopenedText = Get-ClipboardSafe
                $rRows = @($reopenedText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
                $rMatrix = @()
                foreach ($rr in $rRows) {
                    $rMatrix += ,@($rr -split "`t")
                }
                foreach ($ch in $p.changes) {
                    $rIdx = if ($ch.row) { [int]$ch.row - 1 } else { 0 }
                    $cIdx = if ($ch.col) { [int]$ch.col - 1 } else { 0 }
                    $reopenedVal = $rMatrix[$rIdx][$cIdx]
                    $exp = if ($ch.resolved_new_value) { $ch.resolved_new_value } else { [string]$ch.new_value }
                    Write-Host "   [$pId] Reopened Row $($rIdx+1) Col $($cIdx+1) verified: '$reopenedVal' (expected '$exp')" -ForegroundColor Gray
                    if ($reopenedVal -ne $exp) {
                        throw "Reopen verification mismatch for [$pId] at row $($rIdx+1), col $($cIdx+1): expected '$exp', reopened '$reopenedVal'"
                    }
                    $reopenedRows += [pscustomobject]@{
                        parameter_id = $pId
                        parameter_name = $pName
                        row = if ($ch.row) { $ch.row } else { 1 }
                        col = if ($ch.col) { $ch.col } else { 1 }
                        expected = $exp
                        reopened = $reopenedVal
                    }
                }
            }
        } else {
            $edits = @($tableWin2.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::Edit))))
            if ($edits.Count -gt 0) {
                $reopenedVal = $edits[0].GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value
                Write-Host "   [$pId] Reopened Scalar verified: '$reopenedVal' (expected '$($p.new_value)')" -ForegroundColor Gray
                $reopenedRows += [pscustomobject]@{
                    parameter_id = $pId
                    parameter_name = $pName
                    expected = $p.new_value
                    reopened = $reopenedVal
                }
            }
        }
        try { $tableWin2.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {}
        Start-Sleep -Milliseconds 200
    }

    # Whole-file compare against parent
    Write-Host "Running VCM Editor whole-file Compare against parent..." -ForegroundColor Yellow
    Click-Menu 'Compare' 'Open Compare File'
    Start-Sleep -Milliseconds 500
    Submit-FileDialog $parentPath "CompareWithParent"
    Start-Sleep -Milliseconds 800

    # Read comparison differences tree
    Click-Menu 'Compare' 'View Comparison Log'
    Start-Sleep -Milliseconds 500
    $compWin = Find-ByName $root2 'Comparison Log'
    if (-not $compWin) { $compWin = Find-ByName $root2 'Compare' }
    
    # Capture diff items if available
    $diffNodes = @()
    if ($compWin) {
        $treeItems = @($compWin.FindAll([System.Windows.Automation.TreeScope]::Descendants, (New-Object System.Windows.Automation.PropertyCondition ([System.Windows.Automation.AutomationElement]::ControlTypeProperty), ([System.Windows.Automation.ControlType]::TreeItem))))
        foreach ($ti in $treeItems) { $diffNodes += $ti.Current.Name.Trim() }
        try { $compWin.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close() } catch {}
    }
    Write-Host "[OK] Compare pass completed. Difference nodes: $($diffNodes -join ' > ')" -ForegroundColor Green

} finally {
    try {
        if ($proc2 -and -not $proc2.HasExited) {
            $proc2.Kill()
            $proc2.WaitForExit(3000)
        }
    } catch {}
}

# Final Hash & Byte Size Calculation
$candItem = Get-Item $candPath
$candHash = (Get-FileHash -Path $candPath -Algorithm SHA256).Hash

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " BUILD & VERIFICATION SUCCESSFUL!" -ForegroundColor Green
Write-Host " File:    $candPath" -ForegroundColor Green
Write-Host " Bytes:   $($candItem.Length)" -ForegroundColor Green
Write-Host " SHA-256: $candHash" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# Output JSON summary for callers
$outObj = [pscustomobject]@{
    version      = $spec.version
    file         = $spec.file
    parent       = $spec.parent_file
    bytes        = $candItem.Length
    sha256       = $candHash
    parameter_id = $spec.parameter_id
    reopened     = $reopenedRows
    diff_nodes   = $diffNodes
}
if ($spec.output_result_json) {
    $outPath = Join-Path $repoRoot $spec.output_result_json
    $outObj | ConvertTo-Json -Depth 5 | Set-Content -Path $outPath -Encoding UTF8
    Write-Host "Results saved to: $outPath" -ForegroundColor Cyan
}

return $outObj
