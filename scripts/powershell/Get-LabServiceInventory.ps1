# Read-only inventory of allowlisted services on the LOCAL lab machine.
[CmdletBinding()]
param([string]$OutputPath = '.\output\local_inventory.csv')
$allowed = @('Spooler','W32Time','Dnscache')
$items = foreach ($name in $allowed) {
    $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
    [pscustomobject]@{
        host = $env:COMPUTERNAME
        service = $name
        status = if ($null -eq $svc) {'Missing'} else {$svc.Status.ToString()}
        timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
}
$parent=Split-Path $OutputPath -Parent
if ($parent -and -not (Test-Path $parent)) {New-Item -ItemType Directory -Path $parent -Force | Out-Null}
$items | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
Write-Host "Read-only inventory -> $OutputPath"
