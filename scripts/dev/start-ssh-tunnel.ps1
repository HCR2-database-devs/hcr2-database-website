param(
    [Parameter(Mandatory = $true)]
    [string]$SshHost,

    [Parameter(Mandatory = $true)]
    [string]$SshUser,

    [int]$SshPort = 22,

    [string]$RemoteHost = "127.0.0.1",

    [int]$RemotePort = 5432,

    [int]$LocalPort = 54329,

    [string]$IdentityFile
)

$ErrorActionPreference = "Stop"

$sshCommand = Get-Command ssh.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1

$arguments = @(
    "-N",
    "-L", ('{0}:{1}:{2}' -f $LocalPort, $RemoteHost, $RemotePort),
    "-p", "$SshPort",
    "-o", "ExitOnForwardFailure=yes",
    "-o", "ServerAliveInterval=30",
    "-o", "ServerAliveCountMax=3"
)

if (-not [string]::IsNullOrWhiteSpace($IdentityFile)) {
    $arguments += @("-i", $IdentityFile)
}

$arguments += "$SshUser@$SshHost"

Write-Output ("Starting SSH tunnel: localhost:{0} -> {1}:{2} via {3}@{4}" -f $LocalPort, $RemoteHost, $RemotePort, $SshUser, $SshHost)
& $sshCommand.Source @arguments