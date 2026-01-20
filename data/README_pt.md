# 🧪 Gerar Dados de Teste (Mock)

Para testar o sistema sem a criação manual de arquivos, use o script `generate_seeds.py`. Ele cria automaticamente:

* Um arquivo **Excel** estruturado com casos extremos (edge cases).
* Modelos de **Word** e **PowerPoint** com tags Jinja2.
* Um arquivo **ZIP de Assets** com imagens fictícias.

## Como Executar

Execute o seguinte comando no seu terminal:

```bash
docker exec -it logicpaper_core python /data/mock_data/generate_seeds.py
```
