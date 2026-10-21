# Optional Hyper-V provisioning of an empty isolated VM; no Windows installation media included.
[CmdletBinding(SupportsShouldProcess=$true)]
param([string]$Name='LAB-APP1',[string]$Root='C:\HyperV-Labs',[switch]$Execute)
if ($Name -notin @('LAB-DC1','LAB-FS1','LAB-APP1')) {throw 'Lab VM name not allowlisted'}
if (-not $Execute) {Write-Host "DRY_RUN create VM $Name in $Root (requires Hyper-V and install ISO/VHD)";return}
if (-not (Get-Command New-VM -ErrorAction SilentlyContinue)) {throw 'Hyper-V tools unavailable'}
if (-not (Get-VMSwitch -Name 'SelfHeal-Isolated' -ErrorAction SilentlyContinue)) {
  throw 'Create a private SelfHeal-Isolated switch manually before provisioning'
}
if (Get-VM -Name $Name -ErrorAction SilentlyContinue) {throw 'VM already exists'}
if ($PSCmdlet.ShouldProcess($Name, 'Create isolated empty Generation 2 VM')) {
 New-VM -Name $Name -Generation 2 -MemoryStartupBytes 2GB -NewVHDPath (Join-Path $Root "$Name.vhdx") -NewVHDSizeBytes 40GB -SwitchName 'SelfHeal-Isolated' | Out-Null
 Set-VMProcessor -VMName $Name -Count 2
 Write-Host 'Attach authorized Windows installation media and install OS manually.'
}
