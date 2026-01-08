import os
import time
import boto3
import logging
import botocore
import json
from textwrap import dedent
import os
import sys
import glob
sys.path.insert(0, '..') 


from knowledge_base_helper import KnowledgeBasesForAmazonBedrock

kb = KnowledgeBasesForAmazonBedrock() #cria a knowledge base

s3_client = boto3.client('s3')
sts_client = boto3.client('sts')
bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')


region = boto3.session.Session().region_name
account_id = sts_client.get_caller_identity()["Account"]
suffix = f"{region}-{account_id}"
bucket_name = f'agentcore-workshop-{suffix}'


knowledge_base_name = "octank-agent-kb-agentcore"

knowledge_base_description = "KB containing information on octank professors materials"


#Aqui começa a criação da KB ou o retrive dela caso já existir, pode levar alguns minutos
kb_id, ds_id = kb.create_or_retrieve_knowledge_base( 
    knowledge_base_name,
    knowledge_base_description,
    bucket_name
)

print(f"Knowledge Base ID: {kb_id}")
print(f"Data Source ID: {ds_id}")


#Upload dos arquivos do S3 para incrementar na knowledge base
import boto3

def upload_file_to_s3(file_path, bucket_name, object_key=None):
    """Upload a file to S3 bucket"""
    s3_client = boto3.client('s3')
    
    # Check if bucket exists, create if not
    existing_buckets = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]
    if bucket_name not in existing_buckets:
        s3_client.create_bucket(Bucket=bucket_name)
    
    if object_key is None:
        object_key = file_path.split('/')[-1]
    
    s3_client.upload_file(file_path, bucket_name, object_key)
    return f"s3://{bucket_name}/{object_key}"



def upload_all_kb_docs_to_s3(bucket_name):
    """Upload all knowledge base documents to S3"""
    
    # Diretório com todos os arquivos
    docs_dir = "utils/knowledge_base_docs"
    
    # Buscar todos os arquivos .txt
    txt_files = glob.glob(os.path.join(docs_dir, "*.txt"))
    
    uploaded_files = []
    
    for file_path in txt_files:
        try:
            # Nome do arquivo para usar como chave S3
            filename = os.path.basename(file_path)
            object_key = f"documents/{filename}"
            
            # Upload do arquivo
            s3_url = upload_file_to_s3(file_path, bucket_name, object_key)
            uploaded_files.append(s3_url)
            print(f"✓ Uploaded: {filename}")
            
        except Exception as e:
            print(f"✗ Failed to upload {file_path}: {str(e)}")
    
    return uploaded_files

uploaded = upload_all_kb_docs_to_s3(bucket_name)
print(f"Total uploaded: {len(uploaded)} files")


# Start an ingestion job to synchronize data
kb.synchronize_data(kb_id, ds_id)
print('KB synchronization completed\n')

#salva o parametro no SSM Parameter store para consulta depois
param_name = '/app/octank_assistant/agentcore/kb_id'

ssm = boto3.client("ssm")
ssm.put_parameter(Name=param_name, Value=kb_id, Type="String", Overwrite=True)
print(f"Stored {kb_id} in SSM: {param_name}")