# Run locally on an owned disposable Windows lab VM only.
# No network remote execution, no approval automation, no implicit reboot.
[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
param(
  [Parameter(Mandatory=$true)][ValidateSet('Spooler','W32Time','Dnscache')][string]$Service,
  [Parameter(Mandatory=$true)][string]$ApprovalTicket,
  [Parameter(Mandatory=$true)][string]$ExpectedHost,
  [switch]$Execute
)
Set-StrictMode -Version Latest
if ($ExpectedHost -ne $env:COMPUTERNAME) {throw 'Host mismatch. Approval is not for this machine.'}
if ($ApprovalTicket -notmatch '^[A-Za-z0-9-]{8,80}$') {throw 'Invalid ticket reference.'}
$svc=Get-Service -Name $Service -ErrorAction Stop
if ($svc.Status -eq 'Running') {Write-Output "ALREADY_RUNNING $Service";exit 0}
if (-not $Execute) {Write-Output "DRY_RUN Would start $Service (ticket $ApprovalTicket)";exit 0}
if ($PSCmdlet.ShouldProcess($env:COMPUTERNAME, "Start allowlisted service $Service under approved ticket $ApprovalTicket")) {
  Start-Service -Name $Service -ErrorAction Stop
  Start-Sleep -Seconds 2
  $current=(Get-Service -Name $Service).Status
  if ($current -ne 'Running') {throw "Recovery validation failed: $current"}
  Write-Output "RECOVERED $Service ticket=$ApprovalTicket"
}
