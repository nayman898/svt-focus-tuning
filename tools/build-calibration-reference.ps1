$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$folder = Join-Path $root 'reports/calibration-inventory'
$catalog = Get-Content (Join-Path $root 'tunes/revisions.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($r in $catalog.revisions) {
    $file = Join-Path $root ('tunes/' + $r.file)
    if ((Get-Item $file).Length -ne $r.bytes -or (Get-FileHash $file -Algorithm SHA256).Hash -ne $r.sha256) { throw "Tune identity mismatch: $($r.version)" }
}
$records = Get-Content (Join-Path $folder 'v017/inventory.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$index = Import-Csv (Join-Path $folder 'v017/index.csv')
$snap = @{}
foreach ($record in $records) {
    $row = $index | Where-Object parameter_id -eq $record.parameter_id
    $snap[[string]$record.parameter_id] = [ordered]@{
        id = $record.parameter_id; name = $record.name; path = $record.path
        kind = $record.kind; value = $row.displayed_value; cells = @($record.cells)
        description = $record.description; source = ('v017/{0:D3}.json' -f [int]$record.index)
        evidence = 'Captured in v017 at Editor display precision'
    }
}
function Clone($obj) { $obj | ConvertTo-Json -Depth 30 | ConvertFrom-Json }
$snapshots = @{}
$snapshots.v017 = Clone $snap
$snapshots.v016 = Clone $snap
$snapshots.v016.'12115'.value = '520.00'
foreach ($p in $snapshots.v016.PSObject.Properties) { $p.Value.evidence = 'Inherited from v017 through verified whole-file comparison; O2 threshold restored to 520 F' }
$snapshots.v018 = Clone $snapshots.v016
$snapshots.v018.'2291'.value = '1,000'
$dtc = $snapshots.v018.'50'.cells
$p0132 = @($dtc | Where-Object value -eq 'P0132')
if ($p0132.Count -ne 1) { throw 'P0132 row not unique' }
$rowNumber = [regex]::Match($p0132[0].cell, 'Row (\d+)').Groups[1].Value
($dtc | Where-Object cell -eq "Column 2 Row $rowNumber").value = 'MIL Light'
foreach ($p in $snapshots.v018.PSObject.Properties) { $p.Value.evidence = 'Inherited via verified v016/v018 comparisons; DFCO exit and P0132 reporting updated' }
$snapshots.v019 = Clone $snapshots.v018
foreach ($p in $snapshots.v019.PSObject.Properties) { $p.Value.evidence = 'Inherited through verified v018/v019 comparison; only MAF calibration and Notes changed' }
$delta = Get-Content (Join-Path $folder 'v019/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
# Exact clipboard values are retained in a portable evidence file. Normalize all
# four MAF grids to the same Editor unit before comparing, never mix display units.
$maf = Get-Content (Join-Path $folder 'maf-comparison-evidence.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($maf.axes.Count -ne 30 -or $maf.v018.Count -ne 30 -or $maf.v019.Count -ne 30) { throw 'Incomplete MAF evidence' }
foreach ($change in $delta.changes) {
    $i=[int]$change.column-1
    # PS5 JSON decoding may round the last IEEE754 bit differently from parsing
    # clipboard strings. This tolerance is only for serialization consistency.
    if ([Math]::Abs([double]$maf.axes[$i] - [double]$change.voltage) -gt 1e-14 -or
        [Math]::Abs([double]$maf.v018[$i] - [double]$change.old_editor_lb_min) -gt 1e-14 -or
        [Math]::Abs([double]$maf.v019[$i] - [double]$change.new_editor_lb_min) -gt 1e-14) { throw 'MAF evidence disagrees with verified delta' }
}
for ($i=0;$i -lt 30;$i++) {
    if (($i+1) -notin @($delta.changes.column) -and $maf.v018[$i] -ne $maf.v019[$i]) { throw 'Unexpected MAF change' }
}
foreach ($version in @('v016','v017','v018','v019')) {
    $cells = @([ordered]@{cell='Column 0 Row 0';value='Editor lb/min (physical scaling unresolved)'}, [ordered]@{cell='Column 0 Row 1';value='Airflow'})
    for ($i=0; $i -lt $maf.axes.Count; $i++) {
        $col=$i+1
        $cells += [ordered]@{cell="Column $col Row 0";value=[string]$maf.axes[$i]}
        $flow = if ($version -eq 'v019') {$maf.v019[$i]} else {$maf.v018[$i]}
        $cells += [ordered]@{cell="Column $col Row 1";value=[string]$flow}
    }
    $snapshots[$version].'12163'.cells=$cells
    $snapshots[$version].'12163'.evidence='Full-precision Editor clipboard in common display units; physical g/s interpretation unresolved. v016/v017 inherit the unchanged v018 curve.'
}
if ($catalog.revisions.version -contains 'v020') {
    $d20=Get-Content (Join-Path $folder 'v020/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach($version in @('v016','v017','v018','v019')){
        foreach($change in $d20.changes){
            $r=$snapshots[$version].([string]$change.parameter_id)
            ($r.cells | Where-Object cell -eq "Column $($change.column) Row $($change.row)").value=[string]$change.before
        }
    }
    $snapshots.v020=Clone $snapshots.v019
    foreach($change in $d20.changes){
        $r=$snapshots.v020.([string]$change.parameter_id)
        $cell=$r.cells | Where-Object cell -eq "Column $($change.column) Row $($change.row)"
        if(!$cell){throw 'v020 cell missing'}
        $cell.value=[string]$change.after
    }
    foreach($p in $snapshots.v020.PSObject.Properties){$p.Value.evidence='Inherited through verified v019/v020 comparison; base-air900/1000 points reduced5percent inP/N andDrive. Display precision for baseline; exact delta linked.'}
}
if ($catalog.revisions.version -contains 'v021') {
    $d21=Get-Content (Join-Path $folder 'v021/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $snapshots.v021=Clone $snapshots.v019
    foreach($change in $d21.changes){
        $r=$snapshots.v021.([string]$change.parameter_id)
        $cell=$r.cells | Where-Object cell -eq "Column $($change.column) Row $($change.row)"
        if(!$cell){throw 'v021 cell missing'}
        $cell.value=[string]$change.after
    }
    foreach($p in $snapshots.v021.PSObject.Properties){$p.Value.evidence='Inherited from exactv019 through verified full comparison; only7596sensorconversion+Notes changed. v020aircut not inherited.'}
}
if ($catalog.revisions.version -contains 'v022') {
    $d22=Get-Content (Join-Path $folder 'v022/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $snapshots.v022=Clone $snapshots.v021
    $snapshots.v022.'47996'.value=$d22.after
    foreach($p in $snapshots.v022.PSObject.Properties){$p.Value.evidence='Inherited through verified v021/v022 comparison; only idle spark proportional gain47996=0.750 plusNotes changed. v021 remains baseline.'}
}
if ($catalog.revisions.version -contains 'v023') {
    $d23=Get-Content (Join-Path $folder 'v023/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $snapshots.v023=Clone $snapshots.v021
    foreach($change in $d23.changes){
        $r=$snapshots.v023.([string]$change.parameter_id)
        $cell=$r.cells | Where-Object cell -eq "Column $($change.column) Row $($change.row)"
        if(!$cell){throw 'v023 cell missing'}
        $cell.value=[string]$change.after
    }
    foreach($p in $snapshots.v023.PSObject.Properties){$p.Value.evidence='Inherited from exactv021 through verified full comparison; only44579/44578 nominalidle spark12->10plusNotes changed. Gain1.000; v020/v022notinherited.'}
}
if ($catalog.revisions.version -contains 'v024') {
    $fuel=Get-Content (Join-Path $folder 'fuel-base-comparison-evidence.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $d24=Get-Content (Join-Path $folder 'v024/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($fuel.parent_v021_body.Count -ne 8 -or $fuel.v024_body.Count -ne 8) { throw 'Incomplete fuel evidence' }
    foreach($version in @('v016','v017','v018','v019','v020','v021','v022','v023')) {
        for($row=1;$row -le 8;$row++) {
            if($fuel.parent_v021_body[$row-1].Count -ne 10 -or $fuel.v024_body[$row-1].Count -ne 10) { throw 'Incomplete fuel row' }
            for($col=1;$col -le 10;$col++) {
                $cell=$snapshots[$version].'44511'.cells | Where-Object cell -eq "Column $col Row $row"
                $precise=[string]$fuel.parent_v021_body[$row-1][$col-1]
                if([Math]::Abs([double]$cell.value-[double]$precise) -gt 0.0051) { throw 'Fuel evidence exceeds original display rounding' }
                $cell.value=$precise
            }
        }
        $snapshots[$version].'44511'.evidence='Full-precision v021 body capture; unchanged in v016-v023 through verified comparisons. Original axes retained; physical table output lambda.'
    }
    $snapshots.v024=Clone $snapshots.v021
    foreach($change in $d24.changes) {
        $cell=$snapshots.v024.([string]$change.parameter_id).cells | Where-Object cell -eq "Column $($change.column) Row $($change.row)"
        if([Math]::Abs([double]$cell.value-[double]$change.before) -gt 1e-13) { throw 'v024 parent fuel mismatch' }
        $cell.value=[string]$change.after
    }
    for($row=1;$row -le 8;$row++) { for($col=1;$col -le 10;$col++) {
        $cell=$snapshots.v024.'44511'.cells | Where-Object cell -eq "Column $col Row $row"
        if([Math]::Abs([double]$cell.value-[double]$fuel.v024_body[$row-1][$col-1]) -gt 1e-13) { throw 'v024 unexpected fuel body change' }
    }}
    foreach($change in $d24.dtc_changes) {
        $id=$snapshots.v024.'50'.cells | Where-Object cell -eq "Column 0 Row $($change.row)"
        $cell=$snapshots.v024.'50'.cells | Where-Object cell -eq "Column 2 Row $($change.row)"
        if($id.value -ne $change.dtc -or $cell.value -ne $change.before) { throw 'v024 DTC parent mismatch' }
        $cell.value=$change.after
    }
    foreach($p in $snapshots.v024.PSObject.Properties) {$p.Value.evidence='Exact v021 parent; verified saved/reopened comparison changes only 44511 two fuel cells, 50 three DTC modes, Notes. Tested 2026-11-03 with new upstream O2 sensor; provisionally adopted as parent for v025 in covered stationary modes.'}
}
if ($catalog.revisions.version -contains 'v025') {
    $d25 = Get-Content (Join-Path $folder 'v025/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $snapshots.v025 = Clone $snapshots.v024
    if ($maf.v025.Count -ne 30) { throw 'Incomplete v025 MAF evidence' }
    foreach ($change in $d25.changes) {
        $i = [int]$change.column - 1
        if ([Math]::Abs([double]$maf.axes[$i] - [double]$change.voltage) -gt 1e-14 -or
            [Math]::Abs([double]$maf.v019[$i] - [double]$change.old_editor_lb_min) -gt 1e-14 -or
            [Math]::Abs([double]$maf.v025[$i] - [double]$change.new_editor_lb_min) -gt 1e-14) { throw 'v025 MAF evidence disagrees with verified delta' }
    }
    for ($i = 0; $i -lt 30; $i++) {
        if (($i + 1) -notin @($d25.changes.column) -and $maf.v019[$i] -ne $maf.v025[$i]) { throw 'Unexpected v025 MAF change' }
    }
    $cells = @([ordered]@{cell='Column 0 Row 0';value='Editor lb/min (physical scaling unresolved)'}, [ordered]@{cell='Column 0 Row 1';value='Airflow'})
    for ($i = 0; $i -lt $maf.axes.Count; $i++) {
        $col = $i + 1
        $cells += [ordered]@{cell="Column $col Row 0";value=[string]$maf.axes[$i]}
        $cells += [ordered]@{cell="Column $col Row 1";value=[string]$maf.v025[$i]}
    }
    $snapshots.v025.'12163'.cells = $cells
    foreach ($p in $snapshots.v025.PSObject.Properties) {
        $p.Value.evidence = 'Exact v024 parent; verified saved/reopened comparison changes only 12163 MAF Airflow vs. Voltage (columns 6-13, 0.500-1.000 V) and Notes. Tested 2026-11-03; adopted as parent for v026 in covered stationary modes.'
    }
}
if ($catalog.revisions.version -contains 'v026') {
    $d26 = Get-Content (Join-Path $folder 'v026/delta.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $snapshots.v026 = Clone $snapshots.v025
    foreach ($change in $d26.changes) {
        $cell = $snapshots.v026.'32731'.cells | Where-Object cell -eq "Column 1 Row $($change.row)"
        if (-not $cell) { throw "v026 cell missing for row $($change.row)" }
        $cell.value = ('{0:F2}' -f [double]$change.after)
    }
    foreach ($p in $snapshots.v026.PSObject.Properties) {
        $p.Value.evidence = 'Exact v025 parent; verified saved/reopened comparison changes only 32731 Open Loop Fuel TPS Thresh vs. RPM (rows 3 & 4, 2,000-2,500 RPM lifted to 350 counts) and Notes. Prepared candidate, ready for staged testing under docs/v026-regression-test.md.'
    }
}
$data = [ordered]@{generated_utc=[DateTime]::UtcNow.ToString('o'); revisions=$catalog.revisions; snapshots=$snapshots; pending='v026 prepared from exact v025: single-table ECM 32731 Open Loop Fuel TPS Thresh vs. RPM lifted from 0.00 to 350.00 counts at 2,000 and 2,500 RPM. Saved/reopened/compared in VCM Editor; ready for staged testing under docs/v026-regression-test.md.'; installed='v025 tested 2026-11-03; 0 mid-warmup FMEM events, centered 952 RPM warm idle, and 1.5k stoich hold verified; provisionally adopted as parent for v026 in covered stationary modes; no ECU readback.'}
$json=$data | ConvertTo-Json -Depth 40
$json | Set-Content (Join-Path $folder 'revision-reference.json') -Encoding UTF8
$template=Get-Content (Join-Path $PSScriptRoot 'calibration-reference.template.html') -Raw -Encoding UTF8
$tmpHtml = Join-Path $folder 'index.html.tmp'
$template.Replace('__DATA__',$json.Replace('<','\u003c')) | Set-Content $tmpHtml -Encoding UTF8 -NoNewline
Move-Item -Path $tmpHtml -Destination (Join-Path $folder 'index.html') -Force
Write-Output "Built revision reference: $($catalog.revisions.Count) revisions; $($records.Count) parameters in each of $($snapshots.Count) snapshots. All tune hashes match."
