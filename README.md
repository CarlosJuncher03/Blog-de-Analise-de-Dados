# Blog de Análise de Dados

Este projeto é um site de postagens utilizado para criar análises e relatórios que podem ser vinculados a usuários específicos. A principal funcionalidade é permitir que você crie postagens diretamente no site, facilitando a análise de dados para seus clientes. As postagens podem conter documentos e imagens, e você pode especificar quais usuários têm permissão para visualizar cada postagem.

## Funcionalidades

- **Login e Registro de Usuários**
  - Sistema de autenticação com login e registro.
  - Função de logout para desconectar os usuários.
  - Apenas usuários com nível de administrador podem registrar novos usuários.

- **Gerenciamento de Usuários**
  - Administradores podem adicionar, editar e desativar/ativar usuários.
  - Pesquisa de usuários por nome de usuário.

- **Postagens**
  - Criação, edição e exclusão de postagens.
  - Upload de documentos e imagens junto com as postagens.
  - Definição de visibilidade das postagens para usuários específicos.

- **Anotações**
  - Adição, edição e exclusão de anotações.
  - Filtro de anotações por título e data de criação.

- **Dashboard**
  - Adição, edição e exclusão de entradas no dashboard.
  - Pesquisa e filtragem das entradas do dashboard.
  - Definição de visibilidade das entradas do dashboard para usuários específicos.

- **Upload de Arquivos**
  - Upload de arquivos para inclusão em postagens.

## Estrutura do Projeto

|-- main.py
|-- conector.py
|-- templates/
| |-- base.html
| |-- login.html
| |-- register.html
| |-- home.html
| |-- manage_users.html
| |-- posts.html
| |-- post.html
| |-- add_post.html
| |-- edit_post.html
| |-- annotations.html
| |-- dashboard.html
| |-- full_editor.html
| |-- profile.html
|-- static/
| |-- uploads/
| |-- cabecalho/
|-- requirements.txt

bash
Copiar código

## Instalação e Configuração

1. **Clone o Repositório:**
   ```bash
   git clone nesse repositorio
   cd no repositorio
Crie um Ambiente Virtual e Instale as Dependências:

bash
Copiar código
python -m venv venv
source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
Configuração do Banco de Dados:

Configure um banco de dados MySQL e atualize as informações de conexão no arquivo conector.py.
Inicialize o Banco de Dados:

Crie as tabelas necessárias no banco de dados. Utilize o script de criação de tabelas fornecido.
Execute o Aplicativo:

bash
Copiar código
python main.py
Arquivos Principais
main.py:

Contém as rotas principais e a lógica do aplicativo.
Funções para login, registro, gerenciamento de usuários, postagens, anotações e dashboard.
conector.py:

Funções para conectar ao banco de dados e executar consultas de forma segura, protegendo contra SQL Injection.
Detalhes Técnicos
Bibliotecas Utilizadas:

Flask: Framework web para Python.
pymysql: Conector MySQL para Python.
Werkzeug: Utilitário para segurança de senhas.
secrets: Geração de chaves secretas.
Estrutura de Templates:

HTML básico para as páginas de login, registro, gerenciamento de usuários, postagens, anotações e dashboard.
Bootstrap para estilo e layout responsivo.
Upload de Arquivos:

Suporte para upload de arquivos de tipos específicos (txt, pdf, png, jpg, jpeg, gif).
Salvamento seguro de arquivos no servidor.
Segurança:

Senhas criptografadas utilizando generate_password_hash e check_password_hash do Werkzeug.
Proteção contra SQL Injection utilizando consultas parametrizadas.
Contribuição
Contribuições são bem-vindas! Por favor, envie um pull request ou abra uma issue para discutir as mudanças que gostaria de fazer.

Licença
Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.
