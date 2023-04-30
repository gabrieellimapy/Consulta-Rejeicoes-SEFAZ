import csv
import openai
import asyncio
import telegram
import threading
import logging
import nest_asyncio
import configparser
from typing import Dict
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    filters, 
    MessageHandler, 
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler
)

nest_asyncio.apply()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ["Erros de Rejeição"],
    ["Pesquisar"],
    ["Sair"],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

config = configparser.ConfigParser()
config.read('config/config.ini')

tokenbot = config['TESTING']['TOKENBOT']
tokenopneai = config['TESTING']['TOKENOPENAI']

with open('sample_data/rejeicoes.csv', encoding='utf-8') as database:
    leitor_database = csv.reader(database, delimiter=';')
    database_list = list(leitor_database)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    await update.message.reply_text(
        "Oi! Meu nome é sefazopenaibot. \nA partir de agora eu tentarei te ajudar. "
        "\nQual o tópico voce precisa de ajuda?"
        "\nEnvie no chat os tópicos abaixo ou utilize o menu auxiliar."
        "\nErros de Rejeição"
        "\nPesquisar"
        "\nSair",
        reply_markup=markup,
    )

    return TYPING_CHOICE

async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data["choice"] = text
    
    match text:
      case 'Erros de Rejeição':
        await update.message.reply_text(f"Você escolheu {text.lower()}. Poderia me informar somente o código numérico do erro?")
        return TYPING_REPLY 
         
      case 'Sair':
        await update.message.reply_text(
        f"Obrigado por utilizar o meu serviço, para utilizar novamente digite /start aqui no chat.",            
        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
      
      case _:
        await update.message.reply_text(
        "Tópico inválido. "
        "\nQual o tópico voce precisa de ajuda?"
        "\nEnvie no chat os tópicos abaixo ou utilize o menu auxiliar."
        "\nErros de Rejeição"
        "\nPesquisar"
        "\nSair",
        reply_markup=markup)
        return TYPING_CHOICE

async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = update.message.text
    
    if text != 'Sair':
      category = user_data["choice"]
      user_data[category] = text
      del user_data["choice"]
      
      length = len(facts_to_str(user_data))
      cod = facts_to_str(user_data)[length - 4:]
      cod = cod.strip()
      isok = 'n'
      
      while True:
          if any(cod in row for row in database_list):
              for row in database_list:
                  if cod == row[0]:
                      isok = 's'
          else:
            isok = 'n'
          break

      if cod != "" and isok == 's':
        await update.message.reply_text(
        "Legal! Para seu conhecimento, isso é o que você requisitou:"
        f"{facts_to_str(user_data)}Você pode pesquisar o código ou tabém pode alterar o código do erro se quiser.{chr(10)}Envie no chat os tópicos abaixo ou utilize o menu auxiliar.{chr(10)}Erros de Rejeição{chr(10)}Pesquisar{chr(10)}Sair",
        reply_markup=markup,
        )
        return CHOOSING
      else:
        if cod == "":
          await update.message.reply_text(
          "Escolha um tópico que voce precisa de ajuda."
          "\nEnvie no chat os tópicos abaixo ou utilize o menu auxiliar."
          "\nErros de Rejeição"
          "\nPesquisar"
          "\nSair",
          reply_markup=markup,
          )
          return TYPING_CHOICE
        else:
          await update.message.reply_text(
          f"Código não cadastrado, favor utilizar um código válido.{chr(10)}"
          "Escolha um tópico que voce precisa de ajuda."
          "\nEnvie no chat os tópicos abaixo ou utilize o menu auxiliar."
          "\nErros de Rejeição"
          "\nPesquisar"
          "\nSair",        
          reply_markup=markup)
          return TYPING_CHOICE
    else:
      await update.message.reply_text(
      f"Obrigado por utilizar o meu serviço, para utilizar novamente digite /start aqui no chat.",            
      reply_markup=ReplyKeyboardRemove())
      return ConversationHandler.END

async def pesquisar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    print(context.user_data)
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]
    length = len(facts_to_str(user_data))
    cod = facts_to_str(user_data)[length - 4:]
    cod = cod.strip()
     
    while True:
        if any(cod in row for row in database_list):
            for row in database_list:
                if cod == row[0]:
                    isok = 's'
        else:
          isok = 'n'
        break

    if cod != "" and isok == 's':
      response_gpt = consulta_rej(cod)

      await update.message.reply_text(
          f"Aqui está uma possível solução para:{chr(10)} {chr(10)} {response_gpt}{chr(10)}{chr(10)}Obrigado por utilizar o meu serviço, para utilizar novamente digite /start aqui no chat.",
          reply_markup=ReplyKeyboardRemove(),
      )

      user_data.clear()
      return ConversationHandler.END
    
    else:
      await update.message.reply_text(
      f"Código da rejeição não é válido ou não foi informado, favor utilizar um código válido.{chr(10)}"
      "Escolha um tópico que voce precisa de ajuda."
      "\nEnvie no chat os tópicos abaixo ou utilize o menu auxiliar."
      "\nErros de Rejeição"
      "\nPesquisar"
      "\nSair",        
      reply_markup=markup)
      return TYPING_CHOICE



async def sair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print('pesquisar: ' + facts_to_str(context.user_data))
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(
      f"Obrigado por utilizar o meu serviço, para utilizar novamente digite /start aqui no chat.",            
      reply_markup=ReplyKeyboardRemove(),
    )

def consulta_rej(cod):
    openai.api_key = tokenopneai
    while True:
        if any(cod in row for row in database_list):
            for row in database_list:
                if cod == row[0]:
                    prompt = 'Como resolver o código ' + cod + ' ' + row[2]
                    response = openai.Completion.create(
                        engine='text-davinci-003',
                        prompt=prompt,
                        max_tokens=4000
                    )
                    return 'Tipo de Nota: ' + row[1] + '\nErro código: ' + cod + ' - ' + row[2] + '\n' + response.choices[0].text
        else:
            return 'Não encontrado, digite novamente'
        break

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(tokenbot).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Erros de Rejeição)$"), 
                    regular_choice
                ),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Pesquisar$")), 
                    regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Pesquisar$")),
                    received_information,
                )
            ],
        },
        fallbacks=[
            MessageHandler(
                filters.Regex("^Pesquisar$"), pesquisar
                )
            ],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()
