/**
 * Localization Data Store.
 * Contains full text resources for English (en-US) and Portuguese (pt-BR).
 */
const TRANSLATIONS = {
    en: {
        meta: {
            title_home: "LogicPaper | Document Generation Engine",
            title_help: "LogicPaper | Documentation",
            title_history: "LogicPaper | Execution History",
            description: "LogicPaper: A powerful batch processing engine for generating DOCX, PPTX, and PDF documents from Excel/JSON data with advanced logic integration.",
            description_help: "Complete documentation for LogicPaper. Master Jinja2 templating strategies, format data and apply conditional logic.",
            description_history: "View your LogicPaper job execution history, check status, and re-download completed files.",
            keywords: "batch processing, document generation, excel to pdf, excel to word, json to docx, automation, logicpaper"
        },
        navbar: {
            title_main: "Logic",
            title_sub: "Paper",
            subtitle: "Batch Processing Engine v1.3.0",
            link_dashboard: "Dashboard",
            link_history: "History",
            link_help: "How to Use",
            link_api: "API Docs",
            badge_preview: "PREVIEW ONLY",
            badge_online: "SYSTEM ONLINE",
            lang_en: "🇺🇸 EN",
            lang_pt: "🇧🇷 PT"
        },
        dashboard: {
            ingestion: {
                title: "1. Ingestion",
                subtitle: "Drag & Drop Enabled",
                drop_data: {
                    main: "Data Source",
                    sub: "Required (.xlsx or .json)"
                },
                drop_templates: {
                    main: "Templates",
                    sub: "Word, PPTX, Markdown or TXT"
                },
                drop_assets: {
                    main: "Assets Library",
                    sub: "Optional (.zip)"
                },
                btn_validate: "Check Compatibility",
                btn_validating: "Analyzing & Validating..."
            },
            config: {
                title: "2. Configuration",
                lbl_filename: "FILENAME IDENTIFIER",
                placeholder_excel: "Awaiting Excel or JSON file...",
                opt_select_col: "-- Select Identifier Column --",
                lbl_pdf: "Convert Output to PDF",
                lbl_folders: "Group Files in Folders",
                lbl_folders_sub: "Create folder for each row?",
                btn_sample: "🧪 Test (First Row)",
                btn_process: "🚀 Start Processing",
                btn_processing: "⏳ Processing..."
            },
            result: {
                title: "Batch Complete",
                subtitle: "Processing finished successfully",
                click_save: "CLICK TO SAVE",
                download_zip: "DOWNLOAD ZIP ARCHIVE",
                btn_modify: "Modify Settings",
                btn_reset: "Start Fresh"
            },
            preview: {
                title: "DATA_SOURCE_PREVIEW.JSON",
                badge: "READ-ONLY",
                waiting: "Awaiting Excel or JSON file...",
                step1: "Step 1: Reading Data Structure...",
                error: "Error: "
            },
            logs: {
                title: "Execution Logs",
                ready: "System ready. Waiting for command...",
                log_message: "Message",
            }
        },
        history: {
            title: "Execution History",
            btn_refresh: "Refresh",
            col_date: "Date",
            col_input: "Input File",
            col_status: "Status",
            col_stats: "Files",
            col_action: "Action",
            loading: "Loading history...",
            empty: "No jobs found.",
            status_processing: "Processing",
            status_completed: "Completed",
            status_failed: "Failed",
            btn_download: "Download",
        },
        help: {
            toast: "Code copied to clipboard!",
            header: {
                title: "Template Engine Reference",
                desc: "Comprehensive documentation for the LogicPaper formatting engine. Learn how to transform raw Excel data using <strong>Jinja2 Pipes</strong> directly inside your Word, PowerPoint, Markdown or Plain Text templates.",
                btn_back: "Back to Dashboard"
            },
            nav: {
                core: "Core Concepts",
                behavior: "Default Behavior",
                composition: "Chaining & Composition",
                strategies: "Strategies",
                str_string: "Text (String)",
                str_number: "Numbers & Currency",
                str_date: "Dates & Time",
                str_logic: "Logic & Defaults",
                str_bool: "Booleans",
                str_mask: "Privacy & Masking",
                str_image: "Dynamic Images"
            },
            sections: {
                behavior: {
                    title: "Default Behavior",
                    card_title: "What happens if I don't use a formatter?",
                    card_text: "If you use <code>{{ variable }}</code> without a pipe (<code>|</code>), LogicPaper inserts the <strong>Raw Data</strong> exactly as it appears in the Excel cell.",
                    list_dates: "Dates may appear as <code>2023-12-25 00:00:00</code>.",
                    list_money: "Money may appear as <code>1500.5</code> (no symbol, no comma).",
                    list_empty: "Empty cells will appear as empty strings."
                },
                composition: {
                    title: "Chaining & Composition",
                    desc: "You can apply multiple operations in a single filter by listing them as arguments. Operations are executed <strong>sequentially from left to right</strong>.",
                    syntax: "// Syntax",
                    example_comment: "// Example: Clean, Uppercase, and Add Prefix",
                    lbl_input: "Input",
                    lbl_flow: "Process Flow",
                    lbl_output: "Final Output"
                },
                string: {
                    title: "String Strategy",
                    filter_name: "Filter Name:",
                    col_op: "Operation",
                    col_syntax: "Full Template Syntax (Click to Copy)",
                    col_input: "Input Data",
                    col_output: "Output Result",
                    col_details: "Technical Details",
                    op_upper: "Upper",
                    op_lower: "Lower",
                    op_title: "Title Case",
                    op_capitalize: "Capitalize",
                    op_swapcase: "Swap Case",
                    op_trim: "Trim",
                    op_reverse: "Reverse",
                    op_prefix: "Prefix",
                    op_suffix: "Suffix",
                    op_truncate: "Truncate",
                    op_chained: "Chained",
                    op_snake: "Snake Case",
                    op_kebab: "Kebab Case",
                    op_slug: "Slug",
                    desc_upper: "Converts entire string to uppercase.",
                    desc_lower: "Converts entire string to lowercase.",
                    desc_title: "Capitalizes the first letter of every word.",
                    desc_capitalize: "Capitalizes only the first character.",
                    desc_swapcase: "Inverts casing.",
                    desc_trim: "Removes leading and trailing whitespace.",
                    desc_reverse: "Reverses character order.",
                    desc_prefix: "Prepends text.",
                    desc_suffix: "Appends text.",
                    desc_truncate: "Cuts text if exceeds limit.",
                    desc_chained: "Composition: Trim → Upper → Prefix.",
                    desc_snake: "Converts to snake_case.",
                    desc_kebab: "Converts to kebab-case.",
                    desc_slug: "URL-friendly slug (removes special chars)."
                },
                number: {
                    title: "Number & Currency",
                    op_int: "Integer",
                    op_float: "Float",
                    op_round: "Round",
                    op_separator: "Separator",
                    op_usd: "Currency (USD)",
                    op_brl: "Currency (BRL)",
                    op_percent: "Percent",
                    op_scientific: "Scientific",
                    op_human: "Humanize",
                    op_ordinal: "Ordinal",
                    op_spell_en: "Spell Out",
                    desc_int: "Truncates decimals.",
                    desc_float: "Forces N decimal places.",
                    desc_round: "Rounds to precision.",
                    desc_separator: "EU/BR Format (Dot thousands, Comma decimal).",
                    desc_usd: "Locale aware formatting for US Dollar.",
                    desc_brl: "Locale aware formatting for Brazilian Real.",
                    desc_percent: "Multiplies by 100.",
                    desc_scientific: "Scientific notation.",
                    desc_human: "Short scale notation (K, M, B).",
                    desc_ordinal: "Ordinal number conversion.",
                    desc_pad: "Zero padding.",
                    desc_spell: "Numbers to words (supports 'en', 'pt', 'es'...)."
                },
                date: {
                    title: "Date Strategy",
                    op_iso: "ISO Standard",
                    op_short: "Short",
                    op_medium: "Medium",
                    op_long: "Long",
                    op_full: "Full",
                    op_custom: "Custom Pattern",
                    op_year: "Year",
                    op_month: "Month Name",
                    op_add: "Add Days",
                    op_add_years: "Add Years",
                    desc_iso: "Universal ISO 8601 format.",
                    desc_short: "Req. Locale (en, es, pt...).",
                    desc_medium: "Req. Locale (en, es, pt...).",
                    desc_long: "Req. Locale (en, es, pt...).",
                    desc_full: "Req. Locale (en, es, pt...).",
                    desc_custom: "Uses Python strftime syntax.",
                    desc_year: "Extracts only the year.",
                    desc_month: "Full Month Name. Req Locale.",
                    desc_add: "Arithmetic.",
                    desc_add_years: "Arithmetic."
                },
                logic: {
                    title: "Logic & Defaults",
                    op_default: "Default Value",
                    op_status: "Mapping",
                    op_empty: "Empty If",
                    op_fallback: "Fallback",
                    desc_default: "Used when Excel cell is empty.",
                    desc_status: "Maps Keys to Values.",
                    desc_empty: "Hides the value if it matches the argument.",
                    desc_fallback: "Implicit 'Else' value."
                },
                bool: {
                    title: "Boolean Strategy",
                    op_bool: "Bool",
                    op_yesno: "Custom Map",
                    op_check: "Checkbox",
                    desc_bool: "Converts 0/1 to True/False string.",
                    desc_yesno: "Arg 1 is True value, Arg 2 is False value.",
                    desc_check: "Visual checkbox character."
                },
                mask: {
                    title: "Privacy & Masking",
                    op_mask: "Mask",
                    op_email: "Email",
                    op_cc: "Credit Card",
                    op_name: "Name",
                    desc_mask: "Generic pattern.",
                    desc_email: "Obfuscates user part.",
                    desc_cc: "Last 4 digits only.",
                    desc_name: "Initials + ***."
                },
                image: {
                    title: "Dynamic Images",
                    req_title: "Requirement",
                    req_text: "The Excel cell must contain the exact <strong>filename</strong> (e.g., <code>photo.jpg</code>). This file must exist inside the <code>assets.zip</code> uploaded during generation.",
                    ppt_title: "Word vs PowerPoint",
                    ppt_text: "Fully supported in Word (.docx). <br> <span class='text-yellow-500 text-xs'>Note: PowerPoint support is limited to text-replacement only in this version.</span>",
                    desc_resize: "Resizes image to 5cm Width x 3cm Height.",
                    desc_width: "Fixes Width to 5cm, calculates Height.",
                    desc_height: "Fixes Height to 4cm, calculates Width."
                }
            }
        },
        alerts: {
            static_mode: {
                title: "Static Demo Mode",
                html: "<p class='mb-2'>Backend processing is <strong>unavailable</strong> in this live preview.</p>"
            },
            missing_excel: {
                title: "Missing Input",
                text: "Please upload an Excel or JSON file."
            },
            missing_templates: {
                title: "Missing Input",
                text: "Please upload Templates."
            },
            analysis_failed: "Data Analysis failed. Check Excel format.",
            validation_modal: {
                title: "Validation Report",
                title_ok: "Compatibility Confirmed",
                title_fail: "Issues Detected",
                desc_ok: "All templates match the Excel schema.",
                desc_fail: "Some templates contain variables missing from your Excel file.",
                missing_vars: "❌ Missing Variables (in Excel):",
                matched: "variables matched successfully.",
                btn_proceed: "Proceed",
                btn_close: "Understood"
            },
            sample_ready_title: "Sample Ready",
            sample_ready_text: "Check your downloads folder.",
            batch_fail_title: "Batch Failed",
            batch_fail_text: "Check logs for details.",
            files_selected_singular: "{{count}} file selected",
            files_selected_plural: "{{count}} files selected",
            server_error: "Server Error",
            sample_failed_title: "Sample Failed",
            validation_failed_title: "Validation Failed",
            btn_understood: "Understood"
        },
        logs: {
            session_init: "Session initialized.",
            connection_established: "Connection established.",
            template_loaded: "<span class='text-gray-400'>↳ Loaded: {{name}}</span>",
            assets_prepared: "Assets ready.",
            job_queued: "<span class='text-blue-400'>Queued:</span> {{count}} items.",
            task_started: "<span class='text-yellow-500'>Processing started...</span>",
            row_processed: "<span class='text-green-500'>✓ {{percent}}%</span> | {{identifier}} ({{current}}/{{total}})",
            process_complete: "<span class='text-green-400 font-bold uppercase'>Batch Completed</span>",
            inputs_changed: "<span class='text-blue-500 font-bold uppercase tracking-widest block mt-2 mb-1'>Inputs Updated</span>",
            validation_success: "<span class='text-green-400'>Validation successful.</span>",
            sample_start: "<span class='text-purple-400 font-bold uppercase tracking-widest block mt-2 mb-1'>Generating Sample</span>",
            sample_success: "<span class='text-purple-300'>Sample generated.</span>",
            sample_error: "<span class='text-red-400'>Sample Failed:</span> {{error}}",
            batch_init: "<span class='text-green-500 font-bold uppercase tracking-widest block mt-2 mb-1'>Starting Batch</span>",
            connection_lost: "<span class='text-red-500 font-bold'>Connection lost.</span>",
            job_accepted: "<span class='text-blue-400'>Job accepted.</span>",
            request_error: "<span class='text-red-400'>Request Error:</span> {{error}}"
        },
        footer: {
            copy: "LogicPaper © 2025-2026",
            repo: "Source Code",
            api: "API Docs",
            made_by: "Built by",
            author: "Rubens Braz"
        }
    },
    pt: {
        meta: {
            title_home: "LogicPaper | Motor de Geração de Documentos",
            title_help: "LogicPaper | Documentação",
            title_history: "LogicPaper | Histórico de Execuções",
            description: "LogicPaper: Um poderoso motor de processamento em lote para gerar documentos DOCX, PPTX e PDF a partir de dados Excel/JSON com integração de lógica avançada.",
            description_help: "Documentação completa do LogicPaper. Domine estratégias de template Jinja2, formate dados e aplique lógica condicional.",
            description_history: "Visualize o histórico de execuções do LogicPaper, verifique o status e baixe novamente arquivos concluídos.",
            keywords: "processamento em lote, geração de documentos, excel para pdf, excel para word, json para docx, automação, logicpaper"
        },
        navbar: {
            title_main: "Logic",
            title_sub: "Paper",
            subtitle: "Processamento em Lote v1.3.0",
            link_dashboard: "Dashboard",
            link_history: "Histórico",
            link_help: "Como Usar",
            link_api: "Docs API",
            badge_preview: "APENAS VISUALIZAÇÃO",
            badge_online: "SISTEMA ONLINE",
            lang_en: "🇺🇸 EN",
            lang_pt: "🇧🇷 PT"
        },
        dashboard: {
            ingestion: {
                title: "1. Ingestão",
                subtitle: "Arrastar e Soltar Ativado",
                drop_data: {
                    main: "Fonte de Dados",
                    sub: "Obrigatório (.xlsx or .json)"
                },
                drop_templates: {
                    main: "Modelos (Templates)",
                    sub: "Word, PPTX, Markdown ou TXT"
                },
                drop_assets: {
                    main: "Biblioteca de Imagens",
                    sub: "Opcional (.zip)"
                },
                btn_validate: "Verificar Compatibilidade",
                btn_validating: "Analisando e Validando..."
            },
            config: {
                title: "2. Configuração",
                lbl_filename: "IDENTIFICADOR DO ARQUIVO",
                placeholder_excel: "Aguardando arquivo Excel ou JSON...",
                opt_select_col: "-- Selecione a Coluna Identificadora --",
                lbl_pdf: "Converter Saída para PDF",
                lbl_folders: "Agrupar Arquivos em Pastas",
                lbl_folders_sub: "Criar pasta para cada linha?",
                btn_sample: "🧪 Teste (Primeira Linha)",
                btn_process: "🚀 Iniciar Processamento",
                btn_processing: "⏳ Processando..."
            },
            result: {
                title: "Lote Concluído",
                subtitle: "Processamento finalizado com sucesso",
                click_save: "CLIQUE PARA SALVAR",
                download_zip: "BAIXAR ARQUIVO ZIP",
                btn_modify: "Modificar Ajustes",
                btn_reset: "Começar de Novo"
            },
            preview: {
                title: "PRÉVIA_DADOS_EXCEL.JSON",
                badge: "SOMENTE LEITURA",
                waiting: "Aguardando arquivo Excel ou JSON...",
                step1: "Passo 1: Lendo Estrutura dos Dados...",
                error: "Erro: "
            },
            logs: {
                title: "Logs de Execução",
                ready: "Sistema pronto. Aguardando comando...",
                log_message: "Mensagem",
            }
        },
        history: {
            title: "Histórico de Execuções",
            btn_refresh: "Atualizar",
            col_date: "Data",
            col_input: "Arquivo de Entrada",
            col_status: "Status",
            col_stats: "Arquivos",
            col_action: "Ação",
            loading: "Carregando histórico...",
            empty: "Nenhum job encontrado.",
            status_processing: "Processando",
            status_completed: "Concluído",
            status_failed: "Falhou",
            btn_download: "Baixar",
        },
        help: {
            toast: "Código copiado para a área de transferência!",
            header: {
                title: "Referência do Motor de Modelos",
                desc: "Documentação completa para o motor de formatação LogicPaper. Aprenda como transformar dados brutos do Excel usando <strong>Jinja2 Pipes</strong> diretamente dentro dos seus modelos Word, PowerPoint, Markdown ou Plain Text (.txt).",
                btn_back: "Voltar para Dashboard"
            },
            nav: {
                core: "Conceitos Básicos",
                behavior: "Comportamento Padrão",
                composition: "Encadeamento e Composição",
                strategies: "Estratégias",
                str_string: "Texto (String)",
                str_number: "Números e Moeda",
                str_date: "Datas e Hora",
                str_logic: "Lógica e Padrões",
                str_bool: "Booleanos",
                str_mask: "Privacidade e Máscaras",
                str_image: "Imagens Dinâmicas"
            },
            sections: {
                behavior: {
                    title: "Comportamento Padrão",
                    card_title: "O que acontece se eu não usar um formatador?",
                    card_text: "Se você usar <code>{{ variavel }}</code> sem um pipe (<code>|</code>), o LogicPaper insere os <strong>Dados Brutos</strong> exatamente como aparecem na célula do Excel.",
                    list_dates: "Datas podem aparecer como <code>2023-12-25 00:00:00</code>.",
                    list_money: "Dinheiro pode aparecer como <code>1500.5</code> (sem símbolo, sem vírgula).",
                    list_empty: "Células vazias aparecerão como strings vazias."
                },
                composition: {
                    title: "Encadeamento e Composição",
                    desc: "Você pode aplicar múltiplas operações em um único filtro listando-as como argumentos. As operações são executadas <strong>sequencialmente da esquerda para a direita</strong>.",
                    syntax: "// Sintaxe",
                    example_comment: "// Exemplo: Limpar, Maiúsculas e Adicionar Prefixo",
                    lbl_input: "Entrada",
                    lbl_flow: "Fluxo do Processo",
                    lbl_output: "Saída Final"
                },
                string: {
                    title: "Estratégia de Texto",
                    filter_name: "Nome do Filtro:",
                    col_op: "Operação",
                    col_syntax: "Sintaxe Completa (Clique para Copiar)",
                    col_input: "Dados de Entrada",
                    col_output: "Resultado de Saída",
                    col_details: "Detalhes Técnicos",
                    op_upper: "Maiúsculas",
                    op_lower: "Minúsculas",
                    op_title: "Iniciais Maiúsculas",
                    op_capitalize: "Primeira Maiúscula",
                    op_swapcase: "Inverter Caixa",
                    op_trim: "Aparar (Trim)",
                    op_reverse: "Reverso",
                    op_prefix: "Prefixo",
                    op_suffix: "Sufixo",
                    op_truncate: "Truncar",
                    op_chained: "Encadeado",
                    op_snake: "Snake Case",
                    op_kebab: "Kebab Case",
                    op_slug: "Slug (URL)",
                    desc_upper: "Converte toda a string para maiúsculas.",
                    desc_lower: "Converte toda a string para minúsculas.",
                    desc_title: "Capitaliza a primeira letra de cada palavra.",
                    desc_capitalize: "Capitaliza apenas o primeiro caractere da frase.",
                    desc_swapcase: "Inverte maiúsculas e minúsculas.",
                    desc_trim: "Remove espaços em branco no início e no fim.",
                    desc_reverse: "Inverte a ordem dos caracteres.",
                    desc_prefix: "Adiciona texto antes.",
                    desc_suffix: "Adiciona texto depois.",
                    desc_truncate: "Corta o texto se exceder o limite.",
                    desc_chained: "Composição: Trim → Upper → Prefix.",
                    desc_snake: "Converte para snake_case.",
                    desc_kebab: "Converte para kebab-case.",
                    desc_slug: "Slug amigável para URL (remove especiais)."
                },
                number: {
                    title: "Números e Moeda",
                    op_int: "Inteiro",
                    op_float: "Decimal (Float)",
                    op_round: "Arredondar",
                    op_separator: "Separador",
                    op_usd: "Moeda (US)",
                    op_brl: "Moeda (BRA)",
                    op_percent: "Porcentagem",
                    op_scientific: "Científico",
                    op_human: "Humanizar",
                    op_ordinal: "Ordinal",
                    op_spell_en: "Por Extenso",
                    desc_int: "Trunca decimais.",
                    desc_float: "Força N casas decimais.",
                    desc_round: "Arredonda para a precisão.",
                    desc_separator: "Formato EU/BR (Ponto milhar, Vírgula decimal).",
                    desc_usd: "Formatação local para Dólar Americano.",
                    desc_brl: "Formatação local para Real Brasileiro.",
                    desc_percent: "Multiplica por 100.",
                    desc_scientific: "Notação científica.",
                    desc_human: "Notação de escala curta (K, M, B).",
                    desc_ordinal: "Conversão para número ordinal.",
                    desc_pad: "Preenchimento com zeros.",
                    desc_spell: "Converte números em palavras (suporta en, pt, es...)."
                },
                date: {
                    title: "Estratégia de Data",
                    op_iso: "Padrão ISO",
                    op_short: "Curta",
                    op_medium: "Média",
                    op_long: "Texto Longo",
                    op_full: "Completa",
                    op_custom: "Padrão Personalizado",
                    op_year: "Ano",
                    op_month: "Nome do Mês",
                    op_add: "Adicionar Dias",
                    op_add_years: "Adicionar Anos",
                    desc_iso: "Formato universal ISO 8601.",
                    desc_short: "Req. Locale (en, es, pt...).",
                    desc_medium: "Req. Locale (en, es, pt...).",
                    desc_long: "Req. Locale (en, es, pt...).",
                    desc_full: "Req. Locale (en, es, pt...).",
                    desc_custom: "Usa sintaxe strftime do Python.",
                    desc_year: "Extrai apenas o ano.",
                    desc_month: "Nome completo do Mês. Req Locale.",
                    desc_add: "Aritmética.",
                    desc_add_years: "Aritmética."
                },
                logic: {
                    title: "Lógica e Padrões",
                    op_default: "Valor Padrão",
                    op_status: "Mapeamento",
                    op_empty: "Vazio Se",
                    op_fallback: "Fallback",
                    desc_default: "Usado quando a célula do Excel está vazia.",
                    desc_status: "Mapeia Chaves para Valores.",
                    desc_empty: "Oculta o valor se corresponder ao argumento.",
                    desc_fallback: "Valor 'Senão' implícito."
                },
                bool: {
                    title: "Estratégia Booleana",
                    op_bool: "Bool",
                    op_yesno: "Mapa Personalizado",
                    op_check: "Checkbox",
                    desc_bool: "Converte 0/1 para string True/False.",
                    desc_yesno: "Arg 1 é valor Verdadeiro, Arg 2 é valor Falso.",
                    desc_check: "Caractere visual de caixa de seleção."
                },
                mask: {
                    title: "Privacidade e Máscaras",
                    op_mask: "Máscara",
                    op_email: "E-mail",
                    op_cc: "Cartão de Crédito",
                    op_name: "Nome",
                    desc_mask: "Padrão genérico.",
                    desc_email: "Ofusca parte do usuário.",
                    desc_cc: "Apenas últimos 4 dígitos.",
                    desc_name: "Iniciais + ***."
                },
                image: {
                    title: "Imagens Dinâmicas",
                    req_title: "Requisito",
                    req_text: "A célula do Excel deve conter o <strong>nome do arquivo</strong> exato (ex: <code>foto.jpg</code>). Este arquivo deve existir dentro do <code>assets.zip</code> enviado durante a geração.",
                    ppt_title: "Word vs PowerPoint",
                    ppt_text: "Totalmente suportado no Word (.docx). <br> <span class='text-yellow-500 text-xs'>Nota: O suporte ao PowerPoint é limitado apenas à substituição de texto nesta versão.</span>",
                    desc_resize: "Redimensiona para 5cm Largura x 3cm Altura.",
                    desc_width: "Fixa Largura em 5cm, calcula Altura.",
                    desc_height: "Fixa Altura em 4cm, calcula Largura."
                }
            }
        },
        alerts: {
            static_mode: {
                title: "Modo de Demonstração Estático",
                html: "<p class='mb-2'>O processamento de back-end está <strong>indisponível</strong> nesta pré-visualização ao vivo.</p>"
            },
            missing_excel: {
                title: "Entrada Ausente",
                text: "Por favor, carregue um arquivo Excel ou um JSON."
            },
            missing_templates: {
                title: "Entrada Ausente",
                text: "Por favor, carregue os Modelos."
            },
            analysis_failed: "Falha na Análise de Dados. Verifique o formato do Excel.",
            validation_modal: {
                title: "Relatório de Validação",
                title_ok: "Compatibilidade Confirmada",
                title_fail: "Problemas Detectados",
                desc_ok: "Todos os modelos correspondem ao esquema do Excel.",
                desc_fail: "Alguns modelos contêm variáveis ausentes no seu arquivo Excel.",
                missing_vars: "❌ Variáveis Ausentes (no Excel):",
                matched: "variáveis correspondidas com sucesso.",
                btn_proceed: "Prosseguir",
                btn_close: "Entendido"
            },
            sample_ready_title: "Amostra Pronta",
            sample_ready_text: "Verifique sua pasta de downloads.",
            batch_fail_title: "Falha no Lote",
            batch_fail_text: "Verifique os logs para detalhes.",
            files_selected_singular: "{{count}} arquivo selecionado",
            files_selected_plural: "{{count}} arquivos selecionados",
            server_error: "Erro no Servidor",
            sample_failed_title: "Falha na Amostra",
            validation_failed_title: "Falha na Validação",
            btn_understood: "Entendido"
        },
        logs: {
            session_init: "Sessão inicializada.",
            connection_established: "Conexão estabelecida.",
            template_loaded: "<span class='text-gray-400'>↳ Carregado: {{name}}</span>",
            assets_prepared: "Imagens prontas.",
            job_queued: "<span class='text-blue-400'>Fila:</span> {{count}} itens.",
            task_started: "<span class='text-yellow-500'>Iniciando processamento...</span>",
            row_processed: "<span class='text-green-500'>✓ {{percent}}%</span> | {{identifier}} ({{current}}/{{total}})",
            process_complete: "<span class='text-green-400 font-bold uppercase'>Lote Finalizado</span>",
            inputs_changed: "<span class='text-blue-500 font-bold uppercase tracking-widest block mt-2 mb-1'>Entradas Atualizadas</span>",
            validation_success: "<span class='text-green-400'>Validação correta.</span>",
            sample_start: "<span class='text-purple-400 font-bold uppercase tracking-widest block mt-2 mb-1'>Gerando Amostra</span>",
            sample_success: "<span class='text-purple-300'>Amostra gerada.</span>",
            sample_error: "<span class='text-red-400'>Erro na Amostra:</span> {{error}}",
            batch_init: "<span class='text-green-500 font-bold uppercase tracking-widest block mt-2 mb-1'>Iniciando Lote</span>",
            connection_lost: "<span class='text-red-500 font-bold'>Conexão perdida.</span>",
            job_accepted: "<span class='text-blue-400'>Trabalho aceito.</span>",
            request_error: "<span class='text-red-400'>Erro na Requisição:</span> {{error}}"
        },
        footer: {
            copy: "LogicPaper © 2025-2026",
            repo: "Código Fonte",
            api: "Docs API",
            made_by: "Desenvolvido por",
            author: "Rubens Braz"
        }
    }
};