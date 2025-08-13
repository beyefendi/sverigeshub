#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyscript import when 
from pyscript import display
from js import document
from js import console
from io import StringIO

import commission


def log(message):
    # log to pandas dev console
    # print(message)
    # log to JS console
    console.log(message)

def handle_file(event):

    log(f'[+] DEBUG: event: {event}')

    file_input = document.getElementById("file-upload-csv")
    file = file_input.files.item(0)

    log(f'[+] DEBUG: file: {file}')

    if file:
        log(f'[+] DEBUG: File name: {file.name}')
        log(f'[+] DEBUG: File type: {file.type}')
        log(f'[+] DEBUG: File size: {file.size}')

        text_promise = file.text()   # returns a JS Promise (text not a file)
        text_promise.then(process_data)

def process_data(text):

    log(f'[+] DEBUG: Processing CSV...')

    df = commission.load_data(StringIO(text))  # Use StringIO to read the file content

    log(f'[+] DEBUG: DataFrame loaded with {len(df)} rows and {len(df.columns)} columns.')
    
    df = commission.logic_df(df)
    
    # Transpose for better readability in output
    with commission.pd.option_context('display.max_colwidth', None):
        html_output = df.T.to_html(classes="dataframe", border=0)

    output = document.getElementById("output")
    output.innerHTML = html_output

@when ("click", "#btn-upload")
# @when ("change", "#file-upload-csv")
def upload_avanza_csv(event):

    log("[+] DEBUG: Button clicked, processing file...")
    handle_file(event)
    log("[+] DEBUG: File processed.")
    
    #name = document.querySelector("#file-upload-csv").value
    #output = f"Hello, {name}! \nHope you have an awesome day ahead!"
    #output = document.querySelector("#file-upload-csv").files[0]
    #document.querySelector("#output").innerText = output


log("[+] DEBUG: Event listener for button added.")
"""
# Use this instead of upload_avanza_csv function
# Add event listener to file input
document.getElementById("file-upload-csv").addEventListener("change", handle_file)
"""
