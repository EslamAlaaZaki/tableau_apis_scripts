#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import os 
import json
import sys


# In[2]:


def clearConsole():
    command = 'clear'
    if os.name in ('nt', 'dos'):  # If Machine is running on Windows, use cls
        command = 'cls'
    os.system(command)


# In[3]:


def download_bar(current,total):
    bar_length=26
    empty_fill = ' '
    fill = '#'
    progress_percentage=current/total
    
    fill_number=int((progress_percentage*100)/(100/bar_length))
    empty_number=bar_length-fill_number
    
    output="Downloading  |"+fill*fill_number+empty_fill*empty_number+ "|  "+str(int(progress_percentage*100))+ "% "+"["+str(current)+ "/" + str(total) +"]"
    clearConsole()
    print(output)


# In[4]:


def remove_special_characters(input):
    special_characters=["<",">",":","\"","\\","/","|","?","*"]
    for char in special_characters:
        while(input.find(char)!=-1):
            input=input.replace(char,"_")
    return input     


# In[5]:


def sign_in(server_ip,api_version,username,password):
    URL = "http://"+server_ip+"/api/"+api_version+"/auth/signin"
    body="<tsRequest><credentials name=\""+username+"\" password=\""+password+"\" ><site contentUrl=\"\" /></credentials></tsRequest>"
    response=requests.post(URL, data =body).text
    start_index=response.find("token=\"")+len("token=\"")
    end_index=response.find("\"",start_index)
    token=response[start_index:end_index]
    start_index=response.find("site id=\"")+len("site id=\"")
    end_index=response.find("\"",start_index)
    site_id=response[start_index:end_index]
    return site_id,token
    


# In[6]:


def get_projects(server_ip,api_version,site_id,token):
    
    
    projects={}
    page_number=1
    
    while(True):
        
        URL="http://"+server_ip+"/api/"+api_version+"/sites/"+site_id+"/projects?pageSize=1000&pageNumber="+str(page_number)
        page_number=page_number+1
        response=requests.get(URL,headers={"x-tableau-auth":token}).text
        start_index=response.find("<projects>")+len("<projects>")
        end_index=response.find("</projects>",start_index)
        response=response[start_index:end_index]
        if (response.find("</project>")==-1):
            break
        while(response.find("</project>")!=-1):
            
            project=response[:response.find("</project>")]
            response=response[response.find("</project>")+len("</project>"):]
        
        
            start_index=project.find("<project id=\"")+len("<project id=\"")
            end_index=project.find("\"",start_index)
            project_id=project[start_index:end_index]
            project=project[end_index:]
        
            start_index=project.find("name=\"")+len("name=\"")
            end_index=project.find("\"",start_index)
            project_name=remove_special_characters(project[start_index:end_index])
            project=project[end_index:]
        
            if(project.find("parentProjectId=\"")!=-1):
                start_index=project.find("parentProjectId=\"")+len("parentProjectId=\"")
                end_index=project.find("\"",start_index)
                parent_id=project[start_index:end_index]
                parent_path=projects[parent_id]
                projects[project_id]=parent_path+"/"+project_name 
            else:
                projects[project_id]=project_name
        
    return projects


# In[7]:


def get_datasources(server_ip,api_version,site_id,token):
    
    datasources=[]
    page_number=1
    
    while(True):
        URL="http://"+server_ip+"/api/"+api_version+"/sites/"+site_id+"/datasources?pageSize=1000&pageNumber="+str(page_number)
        page_number=page_number+1
        response=requests.get(URL,headers={"x-tableau-auth":token}).text
        if (response.find("</datasource>")==-1):
            break
        #return response
        while(response.find("</datasource>")!=-1):
            datasource={}
            start_index=response.find("id=\"")+len("id=\"")
            end_index=response.find("\"",start_index)
            datasource["datasource_id"]=response[start_index:end_index]
            response=response[end_index:]
        
        
            start_index=response.find("name=\"")+len("name=\"")
            end_index=response.find("\"",start_index)
            datasource["datasource_name"]=response[start_index:end_index]
            response=response[end_index:]
        
            start_index=response.find("project id=\"")+len("project id=\"")
            end_index=response.find("\"",start_index)
            datasource["project_id"]=response[start_index:end_index]
            response=response[end_index:]
        
            start_index=response.find("name=\"")+len("name=\"")
            end_index=response.find("\"",start_index)
            datasource["project_name"]=response[start_index:end_index]
        
            response=response[response.find("</datasource>")+len("</datasource>"):]
            datasources.append(datasource)
        
    return datasources


# In[8]:


def download_datasource(server_ip,api_version,site_id,token,datasource_id,path,file_name):
    
    URL="http://"+server_ip+"/api/"+api_version+"/sites/"+site_id+"/datasources/"+datasource_id+"/content"
    response=requests.get(URL,headers={"x-tableau-auth":token},stream=True)
    
    file_path=path+"/"+ file_name+".tdsx"
        
    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                file.write(chunk)
            #file.write(response.content)


# In[13]:


def download_datasources(server_ip,api_version,site_id,token,download_dir):
    
    datasources=get_datasources(server_ip,api_version,site_id,token)
    current=0
    total=len(datasources)
    
    projects=get_projects(server_ip,api_version,site_id,token)
    download_bar(current,total)    
    for datasource in datasources:
        directory = projects[datasource["project_id"]]
        path = os.path.join(download_dir, directory)
        os.makedirs(path,exist_ok =True)
        download_datasource(server_ip,api_version,site_id,token,datasource["datasource_id"],path,remove_special_characters(datasource["datasource_name"]))
        current=current+1
        download_bar(current,total)


# In[ ]:


if __name__ == "__main__":
    
    f = open(sys.argv[1],)
    
    config = json.load(f)
    # Closing file
    f.close()
    
    server_ip=config['server_ip']
    api_version=config['api_version']
    username=config['username']
    password=config['password']
    download_dir=config['download_dir']
    site_id,token=sign_in(server_ip,api_version,username,password)
    download_datasources(server_ip,api_version,site_id,token,download_dir)
    

