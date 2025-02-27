monitoring = False  # Indica se o bot está ativo
selected_area = None  # Área da tela que será monitorada
log_entries = []  # Lista para armazenar os logs dos lances
# Arquivo de configuração para o Bot de Lances

class Config:
    # Intervalo de tempo aleatório entre os cliques (mínimo e máximo em segundos)
    MIN_CLICK_INTERVAL = 1
    MAX_CLICK_INTERVAL = 60

    # Faixa de cor para detectar o botão verde (valores HSV)
    LOWER_GREEN = (50, 100, 50)  # Verde mais escuro
    UPPER_GREEN = (100, 255, 100)  # Verde mais claro

    # Tamanho da janela do aplicativo
    UI_WIDTH = 400
    UI_HEIGHT = 300
    UI_BG_COLOR = "#f8f9fa"

    # Estilos dos botões
    BUTTON_FONT = ("Arial", 12)
    BUTTON_PADDING = 10
    
    # Estilos dos rótulos
    LABEL_FONT = ("Arial", 14)
    LABEL_BG_COLOR = "#f8f9fa"

    # Nome do arquivo de log padrão
    DEFAULT_LOG_FILENAME = "bot_lances_log.txt"
