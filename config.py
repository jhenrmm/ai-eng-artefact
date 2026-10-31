import os

from dotenv import load_dotenv

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH", "data/políticas_da_loja.pdf")
QUERY = os.getenv("QUERY", "Quantos reais para frete grátis?")