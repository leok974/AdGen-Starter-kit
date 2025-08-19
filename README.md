# AdGen-Starter-kit

## Local Development

To get started with local development, you can use the PowerShell helper script.

### Quickstart

```powershell
Invoke-AdGen "sprite soda on a rock on water surrounded by a valley"
```

## Helper Script for Teammates

This repository includes a PowerShell helper script to streamline the development workflow.

### Setup

To use the `Invoke-AdGen` helper function, you first need to load it into your PowerShell session.

```powershell
. .\scripts\adgen.ps1
```

#### (Optional) Profile Auto-Load for Devs

To make the helper function available in all your PowerShell sessions, you can add it to your profile.

```powershell
Add-Content -Path $PROFILE -Value "`n. `"$((Resolve-Path scripts/adgen.ps1))`""
# Reload your profile or restart your shell for the changes to take effect.
# You can also run the following command to load it in your current session:
. .\scripts\adgen.ps1
```

### Usage

Once the helper script is loaded, you can use the `Invoke-AdGen` function to generate images from a prompt.

```powershell
Invoke-AdGen "a test can on ice"
```

This will generate the image, download the result as a ZIP file, extract it to your Downloads folder, and open the output directory.