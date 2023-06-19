import os
import json
import yaml
import streamlit as st
from streamlit_chat import message
import urllib.request
import openai
import ssl

class GPT:
    def __init__(self,
                config_file: str) -> None:
        ## Load config file
        self.config_file = config_file
        self.load_config()
        ## basic configuration
        self.api_type = self.config['OPENAI']['basic_config']['api_type']
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.api_base = self.config['OPENAI']['basic_config']['api_base']
        self.api_version = self.config['OPENAI']['basic_config']['api_version']
        self.openai_config()
        ## API Engine
        self.engine = self.config['OPENAI']['engine']
        ## Parameter setting
        self.temperature = self.config['OPENAI']['params']['temperature']
        self.max_tokens = self.config['OPENAI']['params']['max_tokens']
        self.top_p = self.config['OPENAI']['params']['top_p']
        self.frequency_penalty = self.config['OPENAI']['params']['frequency_penalty']
        self.presence_penalty = self.config['OPENAI']['params']['presence_penalty']
        self.stop = self.config['OPENAI']['params']['stop']

        ## config for prompt flow
        self.pf_api_key = os.environ.get('PROMPT_FLOW_API_KEY')
        self.deployment_name = self.config['PROMPT_FLOW']['deployment_name']
        self.pf_url = self.config['PROMPT_FLOW']['url']
        self.headers = {'Content-Type':'application/json', 
                        'Authorization':('Bearer '+ self.pf_api_key), 
                        'azureml-model-deployment': self.deployment_name }

    def load_config(self) -> None:
        '''
        Load and extract config yml file.
        '''
        try:
            with open(self.config_file) as file:
                self.config = yaml.safe_load(file)
        except Exception as e:
            print(e)
            raise

    def openai_config(self) -> None:
        openai.api_type = self.api_type
        openai.api_key = self.api_key
        openai.api_base = self.api_base
        openai.api_version = self.api_version

    def get_response(self,
                     chat_history: list,
                     prompt:str) -> str:
        '''
        Get the response from OpenAI.
        '''
        try:
            chat_history.append({"role":"user","content":prompt})
            response = openai.ChatCompletion.create(
                                            engine=self.engine,
                                            messages = chat_history,
                                            temperature=self.temperature,
                                            max_tokens=self.max_tokens,
                                            top_p=self.top_p,
                                            frequency_penalty=self.frequency_penalty,
                                            presence_penalty=self.presence_penalty,
                                            stop=self.stop)
            return response['choices'][0]['message']['content']
        except Exception as e:
            print(e)
            raise

    def get_prompt_flow(self,
                        chat_history: list,
                        prompt:str,) -> str:
        '''
        Get the response from Prompt Flow.
        '''
        try:
            ## set prompt
            data = {
                "chat_history": chat_history,
                "question": prompt
            }
            body = str.encode(json.dumps(data))
            req = urllib.request.Request(self.pf_url, body, self.headers)
            res = urllib.request.urlopen(req)
            return json.loads(res.read().decode('utf-8'))['answer']
        except Exception as e:
            print(e)
            raise

def main():
    gpt = GPT(config_file='./config.yml')
    if "generated" not in st.session_state:
        st.session_state.generated = []
    if "past" not in st.session_state:
        st.session_state.past = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Using "with" notation
    with st.sidebar:
        add_radio = st.radio(
            "Choose the model you want to use",
            ("OPENAI", "PROMPT FLOW")
        )

    with st.form("Chat with GPT"):
        user_message = st.text_area(f"Chat with {add_radio}")
        submitted = st.form_submit_button("Submit")

        if submitted:
            ## for Prompt Flow
            if add_radio == "PROMPT FLOW":
                ## Get the answer
                answer = gpt.get_prompt_flow(chat_history=st.session_state.chat_history,
                                            prompt=user_message)
                ## Store the history
                st.session_state.chat_history.append({"inputs": {"question": user_message},
                                                        "outputs": {"answer": answer}})
            # For OpenAI
            if add_radio == "OPENAI":
                ## Get the answer
                answer = gpt.get_response(chat_history=st.session_state.chat_history,
                                            prompt=user_message)
                st.session_state.chat_history.append({"role":"user","content":user_message})
                st.session_state.chat_history.append({"role":"assistant","content":answer})
            ## Store the messages to show
            st.session_state.past.append(user_message)
            st.session_state.generated.append(answer)

        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])):
                ## User message
                message(st.session_state['past'][i], is_user=True, key=str(i) + "_user")
                ## Bot message１
                message(st.session_state['generated'][i], key=str(i))

if __name__ == '__main__':
    main()