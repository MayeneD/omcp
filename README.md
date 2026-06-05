# OMCP — Orbital Mission Control Platform

Plataforma de monitoramento e controle de missões espaciais.  
Global Solution 2026.1 — Engenharia de Software | FIAP

Desenvolvido por Mayene Doria Rm 558858 E Gabriel Lacerda Rm 556391 
---

## Requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)

Para verificar se você tem Python instalado, abra o terminal e rode:

```
python --version
```

---

## Instalação

**1. Extraia o zip e entre na pasta:**

```
cd omcp_v4
```

**2. Instale a dependência para geração de PDF:**

```
pip install reportlab
```

> Sem o reportlab os relatórios em CSV ainda funcionam normalmente.  
> O PDF só é necessário para exportar relatórios no formato PDF.

---

## Como executar

**3. Inicie o servidor:**

```
python server.py
```

Você verá no terminal:

```
  🛰️  OMCP v4 rodando em http://localhost:3000
  Para PDF: pip install reportlab
  Ctrl+C para parar
```

**4. Abra o navegador e acesse:**

```
http://localhost:3000
```

**5. Para encerrar o servidor**, pressione `Ctrl+C` no terminal.

---

## Usuários de teste

| Email                    | Senha     | Perfil     | Missão |
|--------------------------|-----------|------------|--------|
| c.silva@omcp.gov         | admin123  | Admin      | LUNA-7 |
| a.ferreira@omcp.gov      | op123     | Operador   | LUNA-7 |
| p.mendes@omcp.gov        | eng123    | Engenheiro | LUNA-7 |

---

## Funcionalidades

| Tela           | O que faz                                                              |
|----------------|------------------------------------------------------------------------|
| Login          | Autenticação real com validação de email e senha                       |
| Dashboard      | KPIs, status dos subsistemas e últimos alertas em tempo real           |
| Alertas        | Lista filtrada por severidade, confirmar / escalar / fechar alertas    |
| Sensores       | Cadastrar, editar e excluir sensores com cálculo automático de status  |
| Análise        | Previsão de falhas baseada no estado dos sensores, exportar PDF        |
| Relatórios     | Gerar e baixar PDF ou CSV de alertas, status e análise preditiva       |
| Usuários       | CRUD completo com perfis RBAC e senhas criptografadas                  |
| Auditoria      | Log imutável de todas as ações, exportar CSV                           |
| Configurações  | Salvar nome da plataforma, polling, protocolo e missão ativa           |

---

## Estrutura do projeto

```
omcp_v4/
├── server.py          — servidor HTTP com todas as rotas
├── data/
│   ├── init_db.py     — inicializa o banco SQLite na primeira execução
│   ├── db.py          — camada de acesso aos dados
│   └── pdf_gen.py     — gerador de relatórios PDF e CSV
├── pages/
│   ├── _base.html     — template base (injetado pelo servidor)
│   ├── _topnav.html   — barra de navegação compartilhada
│   ├── _modal-alert.html
│   ├── login.html
│   ├── dashboard.html
│   ├── alertas.html
│   ├── sensores.html
│   ├── preditiva.html
│   ├── relatorio.html
│   ├── usuarios.html
│   ├── auditoria.html
│   └── configuracoes.html
├── css/               — estilos da interface
├── js/                — lógica do frontend
└── relatorios/        — pasta onde os PDFs e CSVs gerados são salvos
```

---

## Banco de dados

O banco `omcp.db` é criado automaticamente na pasta `data/` na primeira vez que você rodar o servidor. Não é necessário instalar nenhum banco de dados separado — o SQLite já vem com o Python.

Se quiser resetar todos os dados para o estado inicial, basta apagar o arquivo `data/omcp.db` e reiniciar o servidor.

---

## Observações

- Os relatórios gerados ficam salvos na pasta `relatorios/` dentro do projeto.
- Todas as ações dos usuários (login, edição, alertas) são registradas automaticamente no log de auditoria.
- O sistema calcula o status dos sensores automaticamente com base nos limiares configurados e gera alertas quando um sensor entra em estado crítico ou alto.
