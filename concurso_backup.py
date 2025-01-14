from numpy import int8
from sklearn.metrics import f1_score
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from pyairtable import Table
import os
import keys


st.set_page_config(page_title='Competencia', layout="wide", page_icon="📒")
OUTPUT_FOLDER = "rules/"

@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
      background-image: url("data:image/png;base64,%s");
      background-size: cover;
    }
    </style>
    ''' % bin_str

# api_key = os.getenv('AIRTABLE_API_KEY')
api_key = keys.APIKEY
table = Table(api_key=api_key, base_id='app89yIsvduofuVNb', table_name='tbl6krugpB1Uvlcpu')

y_true = Table(api_key=api_key, base_id='app89yIsvduofuVNb', table_name='tblXYnOlzZ6yT5eCo')

users = Table(api_key=api_key, base_id='app89yIsvduofuVNb', table_name='tblMaZ0Gkg7Xxe6aa')

dtypes_leaderboard = {"user_name": "object",
                      "file_name": "object",
                      "submit_name_date": "object",
                      "score": "float64",
                      "ranking": "int64",
                      "original_filename": "object"}

records = table.all()
leaderboard = pd.DataFrame.from_records((r['fields'] for r in records))
leaderboard['date'] = pd.to_datetime(leaderboard['date'], format="%Y-%m-%dT%H:%M:%S.%fZ")
leaderboard = leaderboard.sort_values(by = ["score", "date"], ascending=[False, True])
leaderboard['ranking'] = leaderboard["score"].rank(ascending=False, method='first').astype(int)


st.header('Este es el ranking actual')
st.write(leaderboard[['ranking', 'user_name', 'file_name', 'date', 'score']])

records = y_true.all()
y_true_df = pd.DataFrame.from_records((r['fields'] for r in records))
y_true_df = y_true_df.sort_values(by='indice').reset_index(drop=True)
y_true_df['LABELS'] = y_true_df['LABELS'].astype(np.int8)

shape_submit = (len(y_true_df['LABELS']), 1)

records = users.all()
usuarios = pd.DataFrame.from_records((r['fields'] for r in records))
usuarios = usuarios.set_index('indice')

user_name = st.selectbox('Quién sos?', usuarios)
file_name = st.text_input('El nombre que quieras darle')

date = datetime.now()
submit_name_date = user_name + '_' + file_name + '_' + str(date.strftime("%Y_%m_%d-%I:%M:%S_%p"))
uploaded_file = st.file_uploader("Choose a file")

#max_scoring_user_name = leaderboard[leaderboard['user_name'] == user_name]['score'].max()

#max_ranking_user_name = leaderboard[(leaderboard['score'] == max_scoring_user_name) & (leaderboard['user_name'] == user_name)]['ranking'].max()

if uploaded_file is not None:

    try:
        dataframe = pd.read_csv(uploaded_file, header=None, names=['LABELS'], dtype={'LABELS': np.int8})

        if dataframe.shape == shape_submit:

            dataframe['FECHA'] = date
            dataframe['SUBMITION_NAME'] = submit_name_date

            if st.button('Evaluar', key='scoring'):

                scoring_f1 = f1_score(y_true_df['LABELS'],
                                      dataframe['LABELS'])

                if len(file_name) == 0:
                     file_name = uploaded_file.name

                submition_data = {'user_name': user_name,
                                  'file_name': file_name,
                                  'date': date,
                                  'submit_name_date': submit_name_date,
                                  'score': scoring_f1,
                                  'real_filename': uploaded_file.name
                                  }

                submition_df = pd.DataFrame(data=submition_data, index=[0])

                leaderboard = pd.concat([leaderboard, submition_df], axis=0, ignore_index=False)

                leaderboard = leaderboard.sort_values(by=['score', 'date'], ascending=[False, True]).reset_index(drop=True)

                leaderboard['ranking'] = leaderboard["score"].rank(ascending=False, method='first').astype(int)

                submition_data['date'] = submition_data.get('date').isoformat()
                submition_data['preds'] = str(dataframe['LABELS'].to_dict())

                #current_ranking = leaderboard[leaderboard['submit_name_date'] == submit_name_date]['ranking'].max()

                st.header('Tu submit tiene un F1 de: ')
                st.header(round(scoring_f1, 3))

                st.write('Leaderboard actualizado')
                st.write(leaderboard[['ranking', 'user_name', 'file_name', 'date', 'score']])
                table.create(submition_data)


        else:
            st.write(f'Che el tamaño no está bien, es {dataframe.shape} cuando tiene que ser {shape_submit}')
            st.write(dataframe['LABELS'])

    except:
        st.write('Che el formato no está bien, tiene que ser solo una tira de 1 y 0 sin nombre')
