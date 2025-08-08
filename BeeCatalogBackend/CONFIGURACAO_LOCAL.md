# 🏠 Configuração Local - BeeCatalog (Frontend + Backend)

## 🤔 Entendendo CORS para Desenvolvimento Local

Quando você está desenvolvendo localmente, tanto o **frontend** quanto o **backend** rodam em `localhost`, mas em **portas diferentes**:

- 🔙 **Backend Django**: `http://localhost:8000`
- 🎨 **Frontend React/Vue**: `http://localhost:3000` (ou 5173 se for Vite)

O CORS (Cross-Origin Resource Sharing) é necessário porque o navegador considera essas **portas diferentes** como "origens diferentes".

## ⚙️ Configuração para Desenvolvimento Local

### 1. 📝 Editar `.env.production` para Local

Abra o arquivo `.env.production` e configure assim:

```env
# Configurações LOCAIS - BeeCatalog
# Para desenvolvimento local com frontend e backend separados

# Django Core
DJANGO_SETTINGS_MODULE=backbeecatalog.settings_production
DJANGO_ENV=development
DEBUG=True  # ← Para desenvolvimento local
SECRET_KEY=sua_chave_secreta_gerada_automaticamente

# Database - SQLite para desenvolvimento local
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# Redis (opcional para desenvolvimento)
REDIS_URL=redis://localhost:6379/0

# Hosts permitidos - LOCALHOST
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# CORS - URLs LOCAIS DO FRONTEND
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# Email (não necessário para desenvolvimento)
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Sentry (desabilitado para desenvolvimento)
SENTRY_DSN=

# Admin URL
ADMIN_URL=admin/
```

### 2. 🔧 Configuração Alternativa - Arquivo `.env.local`

Ou crie um arquivo específico para desenvolvimento:

```bash
# Criar arquivo para desenvolvimento local
copy .env.production .env.local
```

Edite `.env.local`:

```env
# Configurações LOCAIS - BeeCatalog
DJANGO_SETTINGS_MODULE=backbeecatalog.settings
DEBUG=True
SECRET_KEY=sua_chave_secreta

# SQLite para desenvolvimento
DATABASE_URL=sqlite:///db.sqlite3

# Hosts locais
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# CORS para frontend local
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🚀 Como Rodar Localmente

### 1. 🔙 Iniciar Backend:
```bash
# Opção 1: Com settings padrão (mais simples)
python manage.py runserver

# Opção 2: Com settings de produção (mais realista)
python manage.py runserver --settings=backbeecatalog.settings_production

# Opção 3: Com arquivo .env.local
set DJANGO_SETTINGS_MODULE=backbeecatalog.settings
python manage.py runserver
```

### 2. 🎨 Iniciar Frontend:
```bash
# Ir para o diretório do frontend
cd ..\BeeCatalogFrontend

# Instalar dependências (primeira vez)
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

## 🌐 URLs de Desenvolvimento

Após iniciar ambos os serviços:

- 🔙 **Backend API**: http://localhost:8000
- 🔙 **Django Admin**: http://localhost:8000/admin
- 🎨 **Frontend**: http://localhost:3000 (ou 5173)

## 🔧 Configurações Específicas por Framework

### React (Create React App):
```env
# Frontend roda em: http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### React (Vite):
```env
# Frontend roda em: http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Vue.js:
```env
# Frontend roda em: http://localhost:8080
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

### Next.js:
```env
# Frontend roda em: http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 🛠️ Comandos Úteis para Desenvolvimento

### Verificar configurações:
```bash
python setup_security.py --check
```

### Testar CORS:
```bash
# No navegador, abra o console (F12) e teste:
fetch('http://localhost:8000/api/endpoint')
  .then(response => response.json())
  .then(data => console.log(data))
```

### Ver logs do Django:
```bash
python manage.py runserver --verbosity=2
```

## 🚨 Problemas Comuns e Soluções

### ❌ Erro CORS "Access-Control-Allow-Origin"
```bash
# Verifique se o frontend está na lista CORS_ALLOWED_ORIGINS
# Exemplo: se frontend roda em localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### ❌ Frontend não consegue conectar no backend
```bash
# 1. Verifique se backend está rodando:
curl http://localhost:8000

# 2. Verifique se CORS está configurado
# 3. Verifique se ALLOWED_HOSTS inclui localhost
```

### ❌ Erro "Invalid HTTP_HOST header"
```bash
# Adicione localhost em ALLOWED_HOSTS
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

## 📋 Checklist de Desenvolvimento Local

- [ ] Backend rodando em `http://localhost:8000`
- [ ] Frontend rodando em `http://localhost:3000` (ou outra porta)
- [ ] `ALLOWED_HOSTS` inclui `localhost`
- [ ] `CORS_ALLOWED_ORIGINS` inclui a URL do frontend
- [ ] `DEBUG=True` para desenvolvimento
- [ ] SQLite configurado (mais simples que PostgreSQL)

## 🔄 Migrar de Local para Produção

Quando estiver pronto para produção:

1. **Copie `.env.production` original**
2. **Configure domínios reais**:
   ```env
   ALLOWED_HOSTS=meusite.com,www.meusite.com
   CORS_ALLOWED_ORIGINS=https://meuapp.com
   DEBUG=False
   ```
3. **Configure PostgreSQL**
4. **Execute deploy**

## 💡 Dica Pro

Para alternar facilmente entre desenvolvimento e produção:

```bash
# Desenvolvimento
set DJANGO_SETTINGS_MODULE=backbeecatalog.settings
python manage.py runserver

# Produção local (teste)
set DJANGO_SETTINGS_MODULE=backbeecatalog.settings_production
python manage.py runserver
```

---

**🎯 Resumo**: Para desenvolvimento local, configure `CORS_ALLOWED_ORIGINS` com a URL do seu frontend (ex: `http://localhost:3000`) e `ALLOWED_HOSTS` com `localhost`. Isso permite que frontend e backend se comuniquem mesmo rodando em portas diferentes!