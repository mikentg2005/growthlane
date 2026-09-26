# Builds the site for Cloudflare and zips it. Run from the repo root:
#   powershell -File pipeline\build_cloudflare.ps1
# Then upload the zip in the Cloudflare dashboard: Workers & Pages > growthlane > Deployments/Update
# (or "Upload your static files"). Publishing is a manual step.
$env:Path = 'C:\Ruby33-x64\bin;C:\Ruby33-x64\msys64\ucrt64\bin;' + $env:Path
$out = Join-Path $PSScriptRoot '..\_site_cloudflare'
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
python (Join-Path $PSScriptRoot 'lint_posts.py')
if ($LASTEXITCODE -ne 0) { Write-Output 'Lint failed, not building.'; exit 1 }
jekyll build --source . --destination $out --config "_config.yml,pipeline\cloudflare.yml"
$zip = Join-Path $PSScriptRoot '..\growthlane-site.zip'
python -c "import zipfile,os,sys; r=sys.argv[1]; o=sys.argv[2]; os.path.exists(o) and os.remove(o); z=zipfile.ZipFile(o,'w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(d,f), os.path.relpath(os.path.join(d,f),r).replace(os.sep,'/')) for d,_,fs in os.walk(r) for f in fs]; z.close(); print('Wrote',o)" $out $zip
