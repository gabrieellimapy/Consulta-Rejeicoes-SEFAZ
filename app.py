import csv, tkinter as tk, openai

# ---------------------------- Leitura do arquivo ---------------------------- #
with open('data/rejeicoes.csv', encoding='utf-8') as database:
    leitor_database = csv.reader(database, delimiter=';')
# ------------------------------ Criação da list ----------------------------- #
    database_list = list(leitor_database)
# ----------------------------- Criação da função ---------------------------- #
def consulta_rej(cod): #Função que consulta as rejeições
        while True: #Enquanto for Verdadeira a consulta
            if any (cod in row for row in database_list): #para todo código digitado, é feito uma varredura em cada coluna da lista
                for row in database_list: #para cada coluna
                    if cod == row[0]:#Se o código estiver na coluna de índice 0
                        prompt=f'Como resolver a rejeição {cod} {row[2]}'
                        response = openai.Completion.create(
                                                engine = model,
                                                prompt= prompt,
                                                max_tokens=4000)
                        return '\n Tipo de Nota: ' + row[1] +response.choices[0].text #Imprime o tipo de nota de acordo com a coluna índice 1 e a coluna de índice 2 apresentando a descrição
            else:
                return'Não encontrado, digite novamente'
            break  

# ------------------------------ Criação OPEN AI ----------------------------- #

openai.api_key= #insira aqui sua chave da Open AI

model = 'text-davinci-003'

# --------------------------- Criação da Interface --------------------------- #

class InterfaceGUI(tk.Frame): #Comando incial para uma janela gráfica
    def __init__(self, master=None): #Função que dá início a janela gráfica, trabalha seu próprio master, parâmetro principal
       super().__init__(master) #Inicializa a base tk.Frame 
       self.master = master
       self.master.title('Consulta de Rejeições - SEFAZ') #Define título
       self.pack() #Exibe a Janela
       
       self.create_widgets() #Inicializa a definição dos widgets que vamos adicionar

    def create_widgets(self,height=10): #Trabalha sobre o própria função
        self.cod_label = tk.Label(self, text='Código de Rejeição') #Imprime um Label na tela com o título código da rejeição
        self.cod_label.pack(side='top') #Exibe o widget acima no lado esquerdo da tela
        
        self.cod_entry = tk.Entry(self) #Cria a caixa de Entrada para preenchimento do Código
        self.cod_entry.pack(side='left') #Exbie a caixa de entrada na esquerda da tela
        
        self.consultar_button = tk.Button(self, text='Consultar Código', command=self.consultar_rej) #Cria um botão na tela que permite a consulta de código e executa a função Consultar Rej criada no início do código
        self.consultar_button.pack(side='left') #Exibe o botão no lado esquerdo da tela
        
        self.result_label = tk.Label(self,text='')#Colocando os resultados na tela
        self.result_label.pack(side='top', pady=10)#Centralizando resultados
        
    def consultar_rej(self): #Cria uma função que busca as informações relacionadas ao código de rejeição inserido
        cod = self.cod_entry.get() #Busca o valor da caixa de entrada onde foi inserida as informações
        response_gpt = consulta_rej(cod)
        resultado = response_gpt
        self.result_label.config(text=resultado) #Insere como parâmetro de resposta o resultado da consulta no campo result_label
        self.result_label.config(text=response_gpt, wraplength=600, justify='left')

root = tk.Tk()
app = InterfaceGUI(master=root)
app.mainloop()