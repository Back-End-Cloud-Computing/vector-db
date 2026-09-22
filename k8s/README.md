# vector-db no Kubernetes

Sobe o ChromaDB e três réplicas do vector-db, com Service Discovery entre
eles e o `authorization`.

```
Service vector-db :8002
          |
   Service Discovery
          |
   +------+------+------+
   |             |      |
  Pod           Pod    Pod
   |             |      |
   +------+------+------+
          |
          | chromadb:8000, authorization:8081
          v
   Services correspondentes
```

## Subir

Depende de `authorization` já estar no cluster (repositório próprio):

```bash
kubectl apply -f k8s/chromadb.yaml
kubectl apply -f k8s/vector-db.yaml
```

```bash
kubectl wait --for=condition=ready pod -l app=chromadb --timeout=120s
kubectl wait --for=condition=ready pod -l app=vector-db --timeout=120s
kubectl get pods
```

## Testar a comunicação interna

```bash
kubectl run teste --image=curlimages/curl:latest -it --rm -- sh
```

```sh
# sem token: 401
curl -s -o /dev/null -w "%{http_code}\n" http://vector-db:8002/vector_db/collections

T=$(curl -s -X POST http://authorization:8081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ganjj.com","password":"adminSegura123"}' \
  | sed 's/.*"accessToken":"\([^"]*\)".*/\1/')

# com token: 200 - e por trás dessa chamada o vector-db já fala com o
# chromadb pelo nome do Service
curl -s -o /dev/null -w "%{http_code}\n" http://vector-db:8002/vector_db/collections \
  -H "Authorization: Bearer $T"
```

## Autorrecuperação

```bash
kubectl get pods -l app=vector-db
kubectl delete pod <nome-de-um-pod>
kubectl get pods -l app=vector-db
```

O manifesto declara `replicas: 3`. Ao perder um Pod, o Deployment cria outro
para voltar ao estado declarado, e o Service atualiza os endpoints sozinho.

## Escalar

```bash
kubectl apply -f k8s/vector-db.yaml
```

## Acessar do host

```bash
kubectl port-forward service/vector-db 8002:8002
```

## Acessar via Ingress (sem port-forward por serviço)

```bash
minikube addons enable ingress
kubectl apply -f k8s/ingress.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=120s
```

```bash
IP=$(minikube ip)
PORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
curl -H "Host: vector-db.ganjj.local" http://$IP:$PORT/docs
```

**No WSL2**: encaminhe uma porta só, para o Ingress Controller (não para o
`vector-db` diretamente):

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

Hosts do Windows: `127.0.0.1  vector-db.ganjj.local`. Navegador:
http://vector-db.ganjj.local:8080/docs

## Sobre a imagem

Publicada em [joao2006/vector-db](https://hub.docker.com/r/joao2006/vector-db).
Para publicar uma versão nova:

```bash
docker build -t joao2006/vector-db:1.0.1 .
docker push joao2006/vector-db:1.0.1
```

E atualize a tag em `image:` no `vector-db.yaml`.

## Limitação conhecida

O Chroma roda como Deployment sem volume persistente: se o Pod for recriado,
os embeddings somem. Para o laboratório basta.
