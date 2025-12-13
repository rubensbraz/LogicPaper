/**
 * Localization Data Store.
 * Contains full text resources for English (en-US) and Portuguese (pt-BR).
 */
const TRANSLATIONS = {
    en: {
        navbar: {
            title_main: "Logic",
            title_sub: "Paper",
            subtitle: "Batch Processing Engine v1.0",
            link_dashboard: "Dashboard",
            link_help: "How to Use",
            badge_preview: "PREVIEW ONLY",
            badge_online: "SYSTEM ONLINE",
            lang_en: "🇺🇸 EN",
            lang_pt: "🇧🇷 PT"
        },
        dashboard: {
            ingestion: {
                title: "1. Ingestion",
                subtitle: "Drag & Drop Enabled",
                drop_excel: {
                    main: "Data Source (.xlsx)",
                    sub: "Required"
                },
                drop_templates: {
                    main: "Templates",
                    sub: "Word or PowerPoint"
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
                placeholder_excel: "Awaiting Excel file...",
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
                waiting: "Awaiting Excel file...",
                step1: "Step 1: Reading Excel Structure...",
                error: "Error: "
            },
            logs: {
                title: "EXECUTION_LOGS",
                ready: "System ready. Waiting for command..."
            }
        },
        help: {
            toast: "Code copied to clipboard!",
            header: {
                title: "Template Engine Reference",
                desc: "Comprehensive documentation for the LogicPaper formatting engine. Learn how to transform raw Excel data using <strong>Jinja2 Pipes</strong> directly inside your Word and PowerPoint templates.",
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
                    op_trim: "Trim",
                    op_prefix: "Prefix",
                    op_suffix: "Suffix",
                    op_chained: "Chained",
                    desc_upper: "Converts entire string to uppercase.",
                    desc_lower: "Converts entire string to lowercase.",
                    desc_title: "Capitalizes the first letter of every word.",
                    desc_trim: "Removes leading and trailing whitespace.",
                    desc_prefix: "Prepends text. 2nd Argument is the prefix string.",
                    desc_suffix: "Appends text. 2nd Argument is the suffix string.",
                    desc_chained: "Composition: Trim → Upper → Prefix."
                },
                number: {
                    title: "Number & Currency",
                    op_int: "Integer",
                    op_float: "Float",
                    op_usd: "Currency (US)",
                    op_brl: "Currency (BR)",
                    op_spell_en: "Spell Out (EN)",
                    op_spell_pt: "Spell Out (PT)",
                    op_human: "Humanize",
                    desc_int: "Truncates decimals (does not round up).",
                    desc_float: "Forces N decimal places (Standard dot notation).",
                    desc_usd: "Locale aware formatting for US Dollar.",
                    desc_brl: "Locale aware formatting for Brazilian Real.",
                    desc_spell: "Converts numbers to words.",
                    desc_human: "Short scale notation (K, M, B)."
                },
                date: {
                    title: "Date Strategy",
                    op_iso: "ISO Standard",
                    op_short: "Short (Locale)",
                    op_long: "Long Text",
                    op_custom: "Custom Pattern",
                    op_add: "Add Days",
                    op_complex: "Complex Chain",
                    desc_iso: "Universal ISO 8601 format.",
                    desc_short: "Depends on system locale (default pt_BR).",
                    desc_long: "Fully expanded localized date.",
                    desc_custom: "Uses Python strftime syntax.",
                    desc_add: "Arithmetic. Returns an ISO string by default."
                },
                logic: {
                    title: "Logic & Defaults",
                    op_default: "Default Value",
                    op_status: "Status Mapping",
                    op_empty: "Empty If",
                    op_fallback: "Fallback Map",
                    desc_default: "Used when Excel cell is empty.",
                    desc_status: "Maps Keys to Values. Great for Status Codes.",
                    desc_empty: "Hides the value if it matches the argument.",
                    desc_fallback: "Combines mapping with a default fallback."
                },
                bool: {
                    title: "Boolean Strategy",
                    op_yesno: "Yes/No",
                    op_check: "Visual Checkbox",
                    desc_yesno: "Arg 1 is True value, Arg 2 is False value.",
                    desc_check: "Outputs Wingdings-compatible checkbox characters."
                },
                mask: {
                    title: "Privacy & Masking",
                    op_email: "Email",
                    op_cc: "Credit Card",
                    op_custom: "Custom Pattern",
                    desc_email: "Obfuscates user part, keeps domain.",
                    desc_cc: "Keeps only last 4 digits (PCI Compliant).",
                    desc_custom: "Hashtags (#) are replaced by characters."
                },
                image: {
                    title: "Dynamic Images",
                    req_title: "Requirement",
                    req_text: "The Excel cell must contain the exact <strong>filename</strong> (e.g., <code>photo.jpg</code>). This file must exist inside the <code>assets.zip</code> uploaded during generation.",
                    ppt_title: "Word vs PowerPoint",
                    ppt_text: "Fully supported in Word (.docx). <br> <span class='text-yellow-500 text-xs'>Note: PowerPoint support is limited to text-replacement only in this version.</span>",
                    desc_resize: "Resizes image to 5cm Width x 3cm Height.",
                    desc_width: "Fixes Width to 5cm, calculates Height automatically.",
                    desc_height: "Fixes Height to 4cm, calculates Width automatically."
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
                text: "Please upload an Excel file."
            },
            missing_templates: {
                title: "Missing Input",
                text: "Please upload Templates."
            },
            analysis_failed: "Data Analysis failed. Check Excel format.",
            validation_success: "✅ Analysis Complete. Configuration Unlocked.",
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
            sample_start: "--- STARTED: SAMPLE GENERATION ---",
            sample_success: "✅ Sample generated successfully.",
            sample_ready_title: "Sample Ready",
            sample_ready_text: "Check your downloads folder.",
            sample_error: "❌ Sample Failed: {{error}}",
            batch_init: "--- INITIALIZING BATCH ENGINE ---",
            batch_success: "🏁 Batch processing finished successfully.",
            batch_fail_title: "Batch Failed",
            batch_fail_text: "Check logs for details.",
            connection_lost: "❌ Connection lost with server.",
            inputs_changed: "--- INPUTS CHANGED ---",
            files_selected_singular: "{{count}} file selected",
            files_selected_plural: "{{count}} files selected"
        }
    },
    pt: {
        navbar: {
            title_main: "Logic",
            title_sub: "Paper",
            subtitle: "Motor de Processamento em Lote v1.0",
            link_dashboard: "Painel",
            link_help: "Como Usar",
            badge_preview: "APENAS VISUALIZAÇÃO",
            badge_online: "SISTEMA ONLINE",
            lang_en: "🇺🇸 EN",
            lang_pt: "🇧🇷 PT"
        },
        dashboard: {
            ingestion: {
                title: "1. Ingestão",
                subtitle: "Arrastar e Soltar Ativado",
                drop_excel: {
                    main: "Fonte de Dados (.xlsx)",
                    sub: "Obrigatório"
                },
                drop_templates: {
                    main: "Modelos (Templates)",
                    sub: "Word ou PowerPoint"
                },
                drop_assets: {
                    main: "Biblioteca de Ativos",
                    sub: "Opcional (.zip)"
                },
                btn_validate: "Verificar Compatibilidade",
                btn_validating: "Analisando e Validando..."
            },
            config: {
                title: "2. Configuração",
                lbl_filename: "IDENTIFICADOR DO ARQUIVO",
                placeholder_excel: "Aguardando arquivo Excel...",
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
                title: "PREVIA_DADOS_FONTE.JSON",
                badge: "SOMENTE LEITURA",
                waiting: "Aguardando arquivo Excel...",
                step1: "Passo 1: Lendo Estrutura do Excel...",
                error: "Erro: "
            },
            logs: {
                title: "LOGS_EXECUCAO",
                ready: "Sistema pronto. Aguardando comando..."
            }
        },
        help: {
            toast: "Código copiado para a área de transferência!",
            header: {
                title: "Referência do Motor de Modelos",
                desc: "Documentação completa para o motor de formatação LogicPaper. Aprenda como transformar dados brutos do Excel usando <strong>Jinja2 Pipes</strong> diretamente dentro dos seus modelos Word e PowerPoint.",
                btn_back: "Voltar ao Painel"
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
                    op_trim: "Aparar (Trim)",
                    op_prefix: "Prefixo",
                    op_suffix: "Sufixo",
                    op_chained: "Encadeado",
                    desc_upper: "Converte toda a string para maiúsculas.",
                    desc_lower: "Converte toda a string para minúsculas.",
                    desc_title: "Capitaliza a primeira letra de cada palavra.",
                    desc_trim: "Remove espaços em branco no início e no fim.",
                    desc_prefix: "Adiciona texto antes. O 2º Argumento é a string de prefixo.",
                    desc_suffix: "Adiciona texto depois. O 2º Argumento é a string de sufixo.",
                    desc_chained: "Composição: Trim → Upper → Prefix."
                },
                number: {
                    title: "Números e Moeda",
                    op_int: "Inteiro",
                    op_float: "Decimal (Float)",
                    op_usd: "Moeda (US)",
                    op_brl: "Moeda (BR)",
                    op_spell_en: "Por Extenso (EN)",
                    op_spell_pt: "Por Extenso (PT)",
                    op_human: "Humanizar",
                    desc_int: "Trunca decimais (não arredonda para cima).",
                    desc_float: "Força N casas decimais (Notação de ponto padrão).",
                    desc_usd: "Formatação local para Dólar Americano.",
                    desc_brl: "Formatação local para Real Brasileiro.",
                    desc_spell: "Converte números em palavras.",
                    desc_human: "Notação de escala curta (K, M, B)."
                },
                date: {
                    title: "Estratégia de Data",
                    op_iso: "Padrão ISO",
                    op_short: "Curta (Local)",
                    op_long: "Texto Longo",
                    op_custom: "Padrão Personalizado",
                    op_add: "Adicionar Dias",
                    op_complex: "Cadeia Complexa",
                    desc_iso: "Formato universal ISO 8601.",
                    desc_short: "Depende da localidade do sistema (padrão pt_BR).",
                    desc_long: "Data localizada totalmente expandida.",
                    desc_custom: "Usa sintaxe strftime do Python.",
                    desc_add: "Aritmética. Retorna uma string ISO por padrão."
                },
                logic: {
                    title: "Lógica e Padrões",
                    op_default: "Valor Padrão",
                    op_status: "Mapeamento de Status",
                    op_empty: "Vazio Se",
                    op_fallback: "Mapa de Fallback",
                    desc_default: "Usado quando a célula do Excel está vazia.",
                    desc_status: "Mapeia Chaves para Valores. Ótimo para Códigos de Status.",
                    desc_empty: "Oculta o valor se corresponder ao argumento.",
                    desc_fallback: "Combina mapeamento com um fallback padrão."
                },
                bool: {
                    title: "Estratégia Booleana",
                    op_yesno: "Sim/Não",
                    op_check: "Checkbox Visual",
                    desc_yesno: "Arg 1 é valor Verdadeiro, Arg 2 é valor Falso.",
                    desc_check: "Gera caracteres de caixa de seleção compatíveis com Wingdings."
                },
                mask: {
                    title: "Privacidade e Máscaras",
                    op_email: "E-mail",
                    op_cc: "Cartão de Crédito",
                    op_custom: "Padrão Personalizado",
                    desc_email: "Ofusca a parte do usuário, mantém o domínio.",
                    desc_cc: "Mantém apenas os últimos 4 dígitos (Compatível com PCI).",
                    desc_custom: "Hashtags (#) são substituídas por caracteres."
                },
                image: {
                    title: "Imagens Dinâmicas",
                    req_title: "Requisito",
                    req_text: "A célula do Excel deve conter o <strong>nome do arquivo</strong> exato (ex: <code>foto.jpg</code>). Este arquivo deve existir dentro do <code>assets.zip</code> enviado durante a geração.",
                    ppt_title: "Word vs PowerPoint",
                    ppt_text: "Totalmente suportado no Word (.docx). <br> <span class='text-yellow-500 text-xs'>Nota: O suporte ao PowerPoint é limitado apenas à substituição de texto nesta versão.</span>",
                    desc_resize: "Redimensiona a imagem para 5cm de Largura x 3cm de Altura.",
                    desc_width: "Fixa a Largura em 5cm, calcula a Altura automaticamente.",
                    desc_height: "Fixa a Altura em 4cm, calcula a Largura automaticamente."
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
                text: "Por favor, carregue um arquivo Excel."
            },
            missing_templates: {
                title: "Entrada Ausente",
                text: "Por favor, carregue os Modelos."
            },
            analysis_failed: "Falha na Análise de Dados. Verifique o formato do Excel.",
            validation_success: "✅ Análise Completa. Configuração Desbloqueada.",
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
            sample_start: "--- INICIADO: GERAÇÃO DE AMOSTRA ---",
            sample_success: "✅ Amostra gerada com sucesso.",
            sample_ready_title: "Amostra Pronta",
            sample_ready_text: "Verifique sua pasta de downloads.",
            sample_error: "❌ Falha na Amostra: {{error}}",
            batch_init: "--- INICIANDO MOTOR DE LOTE ---",
            batch_success: "🏁 Processamento em lote finalizado com sucesso.",
            batch_fail_title: "Falha no Lote",
            batch_fail_text: "Verifique os logs para detalhes.",
            connection_lost: "❌ Conexão perdida com o servidor.",
            inputs_changed: "--- ENTRADAS ALTERADAS ---",
            files_selected_singular: "{{count}} arquivo selecionado",
            files_selected_plural: "{{count}} arquivos selecionados"
        }
    }
};