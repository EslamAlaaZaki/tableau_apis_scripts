#!/usr/bin/env python
# coding: utf-8

# In[6]:


import requests
import os 
import json
import sys


# In[7]:


def clearConsole():
    command = 'clear'
    if os.name in ('nt', 'dos'):  # If Machine is running on Windows, use cls
        command = 'cls'
    os.system(command)


# In[8]:


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


# In[9]:


def remove_special_characters(input):
    special_characters=["<",">",":","\"","\\","/","|","?","*"]
    for char in special_characters:
        while(input.find(char)!=-1):
            input=input.replace(char,"_")
    return input     


# In[10]:


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
    


# In[11]:


def get_projects(server_ip,api_version,site_id,token):
    
    
    projects={}
    has_parent=[]
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
                #parent_path=projects[parent_id]
                #projects[project_id]=parent_path+"/"+project_name
                projects[project_id]=project_name
                has_parent.append([project_id,parent_id])
        
            else:
                projects[project_id]=project_name
    
    while(has_parent!=[]):
        for i in has_parent:
            flag=0
            for j in has_parent:
                if i[1]==j[0]:
                    flag=1
            if flag==0:
                parent_path=projects[i[1]]
                projects[i[0]]=parent_path+"/"+projects[i[0]]
                has_parent.remove(i)
                
    return projects


# In[12]:


def get_workbooks(server_ip,api_version,site_id,token):
    
    workbooks=[]
    page_number=1

    while(True):
        URL="http://"+server_ip+"/api/"+api_version+"/sites/"+site_id+"/workbooks?pageSize=1000&pageNumber="+str(page_number)
        page_number=page_number+1
        response=requests.get(URL,headers={"x-tableau-auth":token}).text
        if (response.find("</workbook>")==-1):
            break
    
    #return response
        while(response.find("</workbook>")!=-1):
            workbook={}
            start_index=response.find("workbook id=\"")+len("workbook id=\"")
            end_index=response.find("\"",start_index)
            workbook["workbook_id"]=response[start_index:end_index]
            response=response[end_index:]
        
        
            start_index=response.find("name=\"")+len("name=\"")
            end_index=response.find("\"",start_index)
            workbook["workbook_name"]=response[start_index:end_index]
            response=response[end_index:]
        
            start_index=response.find("project id=\"")+len("project id=\"")
            end_index=response.find("\"",start_index)
            workbook["project_id"]=response[start_index:end_index]
            response=response[end_index:]
        
            start_index=response.find("name=\"")+len("name=\"")
            end_index=response.find("\"",start_index)
            workbook["project_name"]=response[start_index:end_index]
        
            response=response[response.find("</workbook>")+len("</workbook>"):]
            workbooks.append(workbook)
        
    return workbooks


# In[13]:


def download_workbook(server_ip,api_version,site_id,token,workbook_id,path,file_name):
    
    URL="http://"+server_ip+"/api/"+api_version+"/sites/"+site_id+"/workbooks/"+workbook_id+"/content"
    response=requests.get(URL,headers={"x-tableau-auth":token},stream=True)
    file_path=""
    if response.headers.get('content-type')=="application/octet-stream":
        file_path=path+"/"+ file_name+".twbx"
    else:
        file_path=path+"/"+ file_name+".twb"
        
    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                file.write(chunk)
            #file.write(response.content)


# In[ ]:


def download_workbooks(server_ip,api_version,site_id,token,download_dir):
    
    workbooks=get_workbooks(server_ip,api_version,site_id,token)
    current=0
    total=len(workbooks)
    
    projects=get_projects(server_ip,api_version,site_id,token)
    download_bar(current,total)    
    for workbook in workbooks:
        directory = projects[workbook["project_id"]]
        path = os.path.join(download_dir, directory)
        os.makedirs(path,exist_ok =True)
        download_workbook(server_ip,api_version,site_id,token,workbook["workbook_id"],path,remove_special_characters(workbook["workbook_name"]))
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
    download_workbooks(server_ip,api_version,site_id,token,download_dir)
    

