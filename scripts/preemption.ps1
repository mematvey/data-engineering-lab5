$ErrorActionPreference = 'Stop'
$docs = (Get-Content k8s\scheduling.yaml -Raw) -split '(?m)^---\s*$'
$docs[0] | kubectl apply -f -
$docs[1] | kubectl apply -f -
$docs[2] | kubectl apply -f -
kubectl -n hw5 wait --for=condition=ready pod/low-priority --timeout=60s
if ($LASTEXITCODE -ne 0) { throw 'low-priority не готов' }
$docs[3] | kubectl apply -f -
kubectl -n hw5 wait --for=condition=ready pod/high-priority --timeout=60s
if ($LASTEXITCODE -ne 0) { throw 'high-priority не готов' }
kubectl -n hw5 get events --field-selector involvedObject.name=low-priority -o custom-columns=REASON:.reason,MESSAGE:.message --no-headers
