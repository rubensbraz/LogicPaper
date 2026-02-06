# 🗄️ Biblioteca de Templates Persistentes

Este diretório serve como o **repositório central** para templates usados pela **API Headless** (Camada de Integração).

Ao contrário do Dashboard Web (que requer o upload manual de templates para cada sessão), a API espera que os templates sejam pré-carregados nesta pasta para que possam ser referenciados pelo caminho (path) nas suas requisições JSON.

## 🚀 Como Usar

1. **Coloque os Arquivos:** Solte seus templates aqui.
2. **Organize:** Você pode criar subpastas (ex: `contracts/`, `reports/`) para manter tudo organizado.
3. **Referencie:** Nas suas chamadas de API, use o caminho do arquivo relativo a este diretório.

## 🔌 Exemplo de API

**Cenário:**
Você criou uma estrutura de arquivos assim:
`persistent_templates/contracts/service_agreement_v1.docx`

**Requisição:**
Envie o seguinte payload JSON para `POST /api/v1/integration/generate`:

```json
{
  "template_path": "contracts/service_agreement_v1.docx",
  "output_format": "pdf",
  "data": [
    {
      "client_name": "Acme Corp",
      "contract_date": "2024-01-01",
      "amount": 5000.00
    }
  ]
}
```

## 🧪 Testando a API

Você pode testar a API interativamente usando a interface Swagger UI integrada:

* **Documentação:** `http://localhost:8000/docs`

## 🐳 Informações do Volume Docker

Este diretório é mapeado como um volume no `docker-compose.yml`. Qualquer arquivo que você adicionar, remover ou modificar aqui na sua máquina host estará imediatamente disponível dentro do container em execução, sem a necessidade de reiniciar ou reconstruir o serviço.
