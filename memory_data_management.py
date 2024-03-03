# -*- coding: utf-8 -*-
"""
Created on Sun Jul 30 19:47:03 2023

@author: robin
"""
from qdrant_client import QdrantClient as qcqc
from qdrant_client.http import models
import os
from dotenv import load_dotenv
from qdrant_client.http.models import Distance, VectorParams
from langchain.vectorstores import Qdrant
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.embeddings import OpenAIEmbeddings
import numpy as np
from qdrant_client.http.api_client import UnexpectedResponse
from langchain.docstore.document import Document

class mem:
    #this uses langchain integration of qdrant
    def __init__(self, name = 'my cluster', embedding_method='instructor', local =True, UI = None):
        self.name = name
        self.local = local
        self.embedding_method = embedding_method
        if local:
            load_dotenv()
            self.db_path = os.getenv('vectordb_local_path')
            no_db_path = self.db_path == '' or self.db_path is None
            if no_db_path:
                if UI == None:
                    self.db_path = input('enter local path to vector database')
                else:
                    self.db_path = UI.status('vector database path not found',
                                       input_prompt = 'enter local path to vector database')

            self.client = qcqc(path= self.db_path)
        else:
            load_dotenv() #load in the environment
            self.qc_url = os.getenv("qdrant_cliant_url")
            self.qc_apik = os.getenv("qdrant_cliant_api_key")
            #pre-define some error handling variables
            noserv = self.qc_url is None or self.qc_url == ''
            #note that points are vector with extra stuff attached
            if noserv:
                if UI == None:
                    print('no database information')
                    self.qc_url = input("input url: \n")
                    self.qc_apik = input("input api key: \n")
                else:
                    self.qc_url = UI.status('database url missing',input_prompt = "input url: \n")
                    self.qc_apik = UI.status('database api key missing',input_prompt ="input api key: \n")
            self.client = qcqc(url= self.qc_url, api_key= self.qc_apik)
        #figure out how to add stuff to collection
        #then query from the same vectorstore
        #currently the output from chunks is a list of documents without proper metadata, all metadata is local
        self.temp_client = qcqc(location=":memory:")
    def chunk(self,text:str, chunk_size = 1000):
        #return a list of documents for some text given
        overlap = np.floor(chunk_size/10)
        text_splitter = CharacterTextSplitter(
        separator = "\n\n",
        chunk_size = chunk_size,
        chunk_overlap  = overlap,
        length_function = len)
        chunks = text_splitter.split_text(text)
        # docs =  [Document(page_content=chunk, metadata={"source": "local"}) for chunk in chunks]
        return chunks

    def temp_mem(self, text:str, force_recreate = False, embed_instruction: str = 'Represent the document for retrieval: '):
        if self.embedding_method == "open_ai":
            load_dotenv()
            api = os.getenv('OPENAI_API_KEY')
            embeddings = OpenAIEmbeddings(openai_api_key=api,embed_instruction=embed_instruction)
            vsize = 1536
        if self.embedding_method == "instructor":
            vsize = 768
            model_name = "hkunlp/instructor-xl"
            model_kwargs = {'device': 'cuda'}
            encode_kwargs = {'normalize_embeddings': True}
            load_dotenv()
            path = os.getenv('instructor_local_dir')
            os.environ['CURL_CA_BUNDLE'] = ''
            embeddings = HuggingFaceInstructEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                cache_folder = path,
                embed_instruction = embed_instruction)
            
        texts = self.chunk(text)
        docs = [Document(page_content = txt, metadata={"source": "local"}) for txt in texts]
        #collection and points are re_created each time when called
        #all existing points in temperary memory are removed
        vector_store = Qdrant(client= self.temp_client, collection_name="temp_mem", embeddings= embeddings)
        self.temp_vector_store = vector_store
        try:
            vector_store.add_documents(docs)
        except ValueError:
            self.client.recreate_collection(
            collection_name="temp_mem",
            vectors_config=VectorParams(size=vsize, distance=Distance.COSINE),
            hnsw_config=models.HnswConfigDiff())
            vector_store.add_documents(docs)
            
        except UnexpectedResponse:
            self.client.recreate_collection(
            collection_name=self.name,
            vectors_config=VectorParams(size=vsize, distance=Distance.COSINE),
            hnsw_config=models.HnswConfigDiff())
            vector_store.add_documents(docs)
        
    def perm_mem(self, text:str, force_recreate = False, metric = 'cos', meta ={"source": "local"},embed_instruction: str = 'Represent the document for retrieval: '):
        if self.embedding_method == "open_ai":
            vsize = 1536
            load_dotenv()
            api = os.getenv('OPENAI_API_KEY')
            embeddings = OpenAIEmbeddings(openai_api_key=api,embed_instruction=embed_instruction)
            vector_store = Qdrant(client= self.client, collection_name= self.name, embeddings= embeddings)
        if self.embedding_method == "instructor":
            vsize = 768
            model_name = "hkunlp/instructor-xl"
            model_kwargs = {'device': 'cuda'}
            encode_kwargs = {'normalize_embeddings': True}
            load_dotenv()
            path = os.getenv('instructor_local_dir')
            os.environ['CURL_CA_BUNDLE'] = ''
            embeddings = HuggingFaceInstructEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                cache_folder = path,
                embed_instruction = embed_instruction)
            vector_store = Qdrant(client= self.client, collection_name= self.name, embeddings= embeddings)
        #adds texts to permanent memory
        texts = self.chunk(text)
        docs = [Document(page_content = txt, metadata=meta) for txt in texts]
        if metric == 'cos':
            metric = Distance.COSINE
        if metric == 'dot':
            metric = Distance.DOT
        if metric == 'euclid':
            metric = Distance.EUCLID
        if force_recreate:
            self.client.recreate_collection(
            collection_name=self.name,
            vectors_config=VectorParams(size=vsize, distance=metric,on_disk=True),
            hnsw_config=models.HnswConfigDiff(on_disk=True))
        try:
            vector_store.add_documents(docs)
            
        except ValueError:
            self.client.recreate_collection(
            collection_name=self.name,
            vectors_config=VectorParams(size=vsize, distance=metric,on_disk=True),
            hnsw_config=models.HnswConfigDiff(on_disk=True))
            vector_store.add_documents(docs)
            
        except UnexpectedResponse:
            self.client.recreate_collection(
            collection_name=self.name,
            vectors_config=VectorParams(size=vsize, distance=metric,on_disk=True),
            hnsw_config=models.HnswConfigDiff(on_disk=True))
            vector_store.add_documents(docs)
        if not self.local:
            print('checking cloud uploads:')
            status = self.client.get_collection(collection_name=self.name)
            print('status: ',status)
        self.perm_vector_store = vector_store

    def load_vector_store(self,embed_instruction:str ='Represent the document for retrieval: ',perma = True):
        if self.embedding_method == "open_ai":
            load_dotenv()
            api = os.getenv('OPENAI_API_KEY')
            embeddings = OpenAIEmbeddings(openai_api_key=api,embed_instruction=embed_instruction)
        if self.embedding_method == "instructor":
            model_name = "hkunlp/instructor-xl"
            model_kwargs = {'device': 'cuda'}
            encode_kwargs = {'normalize_embeddings': True}
            load_dotenv()
            path = os.getenv('instructor_local_dir')
            os.environ['CURL_CA_BUNDLE'] = ''
            embeddings = HuggingFaceInstructEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                cache_folder = path,
                embed_instruction = embed_instruction)
        if perma:
            vector_store = Qdrant(client= self.client, collection_name= self.name, embeddings= embeddings)
        else:
            vector_store = Qdrant(client= self.temp_client, collection_name="temp_mem", embeddings= embeddings)
        return vector_store

    def query(self, query:str,query_instruction: str = 'Represent the question for retrieving supporting documents: ',limit = 1):
        #note that client is only avalible if permanent memory was extablished
        #IE can't query if there isn't anything
        
        if self.embedding_method == "open_ai":
            load_dotenv()
            api = os.getenv('OPENAI_API_KEY')
            embeddings = OpenAIEmbeddings(openai_api_key=api,query_instruction=query_instruction)
        if self.embedding_method == "instructor":
            model_name = "hkunlp/instructor-xl"
            model_kwargs = {'device': 'cuda'}
            encode_kwargs = {'normalize_embeddings': True}
            load_dotenv()
            path = os.getenv('instructor_local_dir')
            os.environ['CURL_CA_BUNDLE'] = ''
            embeddings = HuggingFaceInstructEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                cache_folder = path,
                query_instruction = query_instruction)
        results = self.client.search(collection_name = self.name,
                                query_vector = embeddings.embed_query(query),
                                limit = limit,
                                with_payload=True,)
        return results

def main():
    m = mem(name = 'agents')
    res = m.query('some one who tell jokes',limit=1)
    m.client.close()
    return res
if __name__ == '__main__':
    ans = main()