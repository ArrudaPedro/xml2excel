import xml.etree.ElementTree as ET
import os
import csv
import tkinter as tk
from tkinter import messagebox, filedialog, ttk 
import threading

# --- FUNÇÕES DE LÓGICA ---

def normalizar(texto):
    if not texto: return ""
    mapa_acentos = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ã": "A", "Õ": "O", "Â": "A", "Ê": "E", "Î": "I", "Ô": "O", "Û": "U", "Ç": "C"}
    texto = texto.upper()
    for acento, sem_acento in mapa_acentos.items():
        texto = texto.replace(acento, sem_acento)
    return texto

def buscar_data(root):
    for tag in ['.//{*}dhEmi', './/{*}dEmi', './/{*}dSaiEnt']:
        el = root.find(tag)
        if el is not None and el.text:
            return el.text[:10]
    for el in root.iter():
        if any(nome in el.tag for nome in ['dhEmi', 'dEmi']):
            if el.text: return el.text[:10]
    return "N/A"

def iniciar_processamento():
    termo_busca = entry_busca.get().strip()
    diretorio = filedialog.askdirectory()
    
    if not diretorio:
        return

    # Inicia a Thread para não travar a tela
    threading.Thread(target=tarefa_pesada, args=(diretorio, termo_busca), daemon=True).start()

def tarefa_pesada(diretorio, termo_busca):
    # 1. Preparação
    arquivos = [f for f in os.listdir(diretorio) if f.endswith('.xml')]
    total_arquivos = len(arquivos)
    
    if total_arquivos == 0:
        window.after(0, lambda: messagebox.showwarning("Aviso", "Nenhum arquivo XML encontrado na pasta."))
        return

    # Configura a interface para o modo "carregando"
    window.after(0, preparar_interface_loading, total_arquivos)

    resultados = []
    termos_filtro = normalizar(termo_busca).split()

    # 2. Processamento
    for i, nome_arquivo in enumerate(arquivos):
        try:
            tree = ET.parse(os.path.join(diretorio, nome_arquivo))
            root = tree.getroot()
            data_val = buscar_data(root)
            
            fornecedor = root.find('.//{*}emit/{*}xNome')
            forn_val = fornecedor.text if fornecedor is not None else "N/A"

            itens = root.findall('.//{*}det')
            for item in itens:
                prod = item.find('{*}prod')
                if prod is not None:
                    xProd = prod.find('{*}xProd').text
                    if all(termo in normalizar(xProd) for termo in termos_filtro):
                        qnt = round(float(prod.find('{*}qCom').text), 3)
                        vun = round(float(prod.find('{*}vUnCom').text), 2)
                        vprod = round(float(prod.find('{*}vProd').text), 2)

                        resultados.append({
                            'Data': data_val, 'Fornecedor': forn_val, 'Produto': xProd,
                            'Peso_KG': str(qnt).replace('.', ','),
                            'Preco_Unit_KG': str(vun).replace('.', ','),
                            'Total_Item': str(vprod).replace('.', ','),
                            'Arquivo': nome_arquivo
                        })
        except:
            pass
        
        # Atualiza a barra de progresso na tela principal
        progresso = int(((i + 1) / total_arquivos) * 100)
        window.after(0, atualizar_progresso, progresso, i + 1, total_arquivos)

    # 3. Finalização
    if resultados:
        nome_csv = f"relatorio_{termo_busca.replace(' ', '_') or 'geral'}.csv"
        with open(nome_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=resultados[0].keys(), delimiter=';')
            writer.writeheader()
            writer.writerows(resultados)
        window.after(0, finalizar_sucesso, nome_csv, len(resultados))
    else:
        window.after(0, finalizar_erro)

# --- FUNÇÕES AUXILIARES DA INTERFACE ---

def preparar_interface_loading(total):
    button_read.config(state="disabled")
    progress_bar['value'] = 0
    label_status.config(text=f"⚙️ Iniciando leitura de {total} arquivos...", fg="blue")

def atualizar_progresso(valor, atual, total):
    progress_bar['value'] = valor
    label_status.config(text=f"⚙️ Processando: {atual} de {total}")

def finalizar_sucesso(nome, qtd):
    button_read.config(state="normal")
    label_status.config(text="✅ Concluído!", fg="green")
    messagebox.showinfo("Sucesso", f"Relatório '{nome}' gerado!\n{qtd} itens encontrados.")

def finalizar_erro():
    button_read.config(state="normal")
    label_status.config(text="❌ Nada encontrado.", fg="red")
    messagebox.showwarning("Aviso", "Nenhum produto corresponde à busca.")

# --- INTERFACE GRÁFICA ---

window = tk.Tk()
window.title("XML Reader Ultra")
window.geometry("450x380")

tk.Label(window, text="O que deseja buscar?", font=("Arial", 11, "bold"), pady=15).pack()
entry_busca = tk.Entry(window, width=35, font=("Arial", 12))
entry_busca.insert(0, "FILE MIGNON")
entry_busca.pack(pady=5)

# Barra de Progresso
progress_bar = ttk.Progressbar(window, orient="horizontal", length=350, mode="determinate")
progress_bar.pack(pady=25)

# Label de Status
label_status = tk.Label(window, text="Aguardando comando...", fg="gray", font=("Arial", 10))
label_status.pack()

button_read = tk.Button(window, text="SELECIONAR PASTA E EXECUTAR", 
                       bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                       width=35, height=2, command=iniciar_processamento)
button_read.pack(pady=25)

window.mainloop()