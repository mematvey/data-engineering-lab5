# data-engineering-lab5

Домашнее задание 5 по инженерии данных, Kubernetes, вариант 9 (разработчик на мобильных платформах)
Текст отчёта лежит в docs/, журналы запусков в outputs, результаты расчёта и замеров в results
Нужны Docker Desktop, kind, kubectl, uv, CSV из ДЗ 2 и результат MapReduce results/mapreduce/stack_2.csv из ДЗ 3
Для переноса JSON из хранилища ДЗ 2 нужен rclone
Тома RustFS используют emptyDir, поэтому после пересоздания Pod данные нужно загрузить заново

```
kind create cluster --name hw5-mematvey --kubeconfig .\kubeconfig --wait 180s
$env:KUBECONFIG = (Resolve-Path .\kubeconfig).Path
uv sync
docker build -t hw5-pairs:local .
kind load docker-image hw5-pairs:local --name hw5-mematvey
kubectl apply -f k8s\storage.yaml
kubectl -n hw5 rollout status deployment/rustfs-six --timeout=120s
```

Проброс порта в отдельном окне:

```
$env:KUBECONFIG = (Resolve-Path .\kubeconfig).Path
kubectl -n hw5 port-forward svc/rustfs-six 19100:9000
```

```
$env:S3_ENDPOINT = 'http://127.0.0.1:19100'
uv run python src\upload.py ..\task2\data\it_vacancies_2024.csv
kubectl apply -f k8s\oom.yaml
kubectl apply -f k8s\pairs.yaml
kubectl -n hw5 wait --for=condition=complete job/pairs --timeout=120s
kubectl apply -f k8s\reduce.yaml
kubectl -n hw5 wait --for=condition=complete job/pairs-reduce --timeout=120s
kubectl -n hw5 logs job/pairs-reduce
uv run python src\compare.py ..\task3\results\mapreduce\stack_2.csv
powershell scripts\preemption.ps1
kubectl apply -f k8s\cpu-wait.yaml
kubectl apply -f k8s\quota.yaml
kubectl apply -f k8s\quota-pods.yaml
```
