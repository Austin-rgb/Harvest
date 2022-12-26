import re,sys,requests,os,json
from smtplib import SMTP 
def scrap(data,domain):
    title=re.compile(r'<title>.+</title>')
    target_pattern=re.compile(f'<a href="[\S]+?"')
    z=target_pattern.findall(data)
    d=title.findall(data)
    if len(d)>0:
        t=d[0]
        t=t.removeprefix('<title>')
        t=t.removesuffix('</title>')
    else:
        t=''
    for i in range(len(z)):
        z[i]=z[i].removeprefix('<a href="')
        z[i]=z[i].removesuffix('"')
    linkdicts=[]
    j=0
    for i in z:
        if i.startswith('/'):
            z[j]=domain+i
        j+=1
    for i in z:
        d1=dict()
        d1['isinternal']=i.__contains__(domain)
        d1['url']=i
        linkdicts.append(d1)
    return t,linkdicts
fs=os.listdir()
if fs.__contains__('harvest_context.json'):
    context_file=open('harvest_context.json','r+')
    context=json.loads(context_file.read())
    domain=context['domain']
    discovered=context['discovered']
    openned=context['openned']
    removed=context['removed']
    print('Continuing with the paused project')
else:
    domain=input('Enter domain of the website e.g https://www.example.com\n')
    openned=[]
    discovered=[]
    removed=[]
try:
    t,discovered=scrap(requests.get(domain).text,domain)
except:
    context={'domain':domain,'discovered':discovered,'openned':openned,'removed':removed}
    os.remove('harvest_context.json')
    open('harvest_context.json','x+').write(json.dumps(context))
    print('Connection was reset please reconnect')
    sys.exit()
d1={'title':t,'link':domain,'isinternal':True}
openned.append(d1)
while len(discovered)>len(openned):
    for d in discovered:
        if not openned.__contains__(d):
            if d['isinternal']:
                try:
                    data=requests.get(d['url']).text
                except:
                    print('Connection was reset, please reconnect')
                    context={'domain':domain,'discovered':discovered,'openned':openned,'removed':removed}
                    try:
                        os.remove('harvest_context.json')
                    except:
                        pass
                    open('harvest_context.json','x+').write(json.dumps(context))
                    print('Successfully saved project context')
                    sys.exit()
                t,links=scrap(data,domain)
                for l in links:
                    if not discovered.__contains__(l):
                        discovered.append(l)
                d1={'title':t,'url':d['url'],'isinternal':d['isinternal']}
                openned.append(d1)
            else:
                removed.append(d)
                discovered.remove(d)
        os.system('clear')
        print(f'Discovered {len(discovered)+len(removed)} links\t Openned {len(openned)} links\t removed {len(removed)} noninternal links')
msg='<!doctype html><html><head><title>Scraped links</title></head><body><table><thead><td>Text</td><td>URL</td><td>isinternal</td></thead>'
for o in openned:
    try:
        msg+='<tr><td>'+o['title']+'</td>'
        msg+='<td>'+o['url']+'</td>'
        msg+='<td>'+o['isinternal']+'</td></tr>'
    except:
        continue
msg+='</table></body></html>'
try:
    file=open('harvested_links.html','x+')
    file.write(msg)
    file.close()
except:
    pass
print('Links file compiled succesfully.')
if context.keys().__contains__('email_server'):
    server=context['email_server']
    fromaddr=context['fromaddr']
    toaddr=context['toaddr']
else:
    server=input('Enter email server e.g example.com\n')
    context['email_server']=server
    fromaddr=input('Sending email from:\n')
    toaddr=input('Sending email to:\n')
    context['fromaddr']=fromaddr
    context['toaddr']=toaddr
    
final=SMTP(server)
final.login(fromaddr,'$Ost@prof12')
final.sendmail(fromaddr,toaddr,msg)
#os.remove('harvest_context.json')
#open('harvest_context.json','x+').write(json.dumps(context))
print('Could not send email, please confirm that you are connected.')

