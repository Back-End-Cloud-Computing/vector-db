# Chart Helm — `vector-db`

Mesmo desenho do [`k8s/`](../../k8s/README.md): Deployment `vector-db` (3 réplicas, anotações do Prometheus), Service
`vector-db:8002`, ConfigMap e ChromaDB opcional. Os valores que mudam entre ambientes estão em
[`values.yaml`](values.yaml).

Diferenças em relação aos charts com entrada pública:

- **Sem Ingress e sem `host`**: o vector-db é interno, só o `product` o chama pelo Service.
- **Sem `existingSecret`**: o serviço não tem segredo próprio; valida o JWT com a chave pública do `authorization`,
  que precisa estar instalado antes.

```bash
helm lint helm/vector-db
helm upgrade --install vector-db helm/vector-db
kubectl get pods -w
helm uninstall vector-db
```

| Quero | Faço |
|---|---|
| Outra versão da imagem | `--set image.tag=1.1.1` |
| Mais réplicas | `--set replicaCount=5` |
| ChromaDB externo | `--set chromadb.enabled=false --set config.CHROMA_HOST=<host>` |

Testado em 24/10/2026 num cluster `kind` limpo (Kubernetes 1.37, Helm 4.3): `helm lint` limpo, `helm install` com o
`values.yaml` padrão sobe 3 pods `vector-db` `1/1` e o ChromaDB, sem nenhum restart: as réplicas esperam o Chroma
ficar pronto (retry na conexão) e `/health` e `/metrics` respondem 200 pelo Service.
