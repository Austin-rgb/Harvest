import re,sys,requests,os,json
from smtplib import SMTP
def save(context):
    try:
        os.remove('harvest_context.json')
    except:
        pass
    open('harvest_context.json','x+').write(json.dumps(context))
def scrap(data,domain):
    title=re.compile(r'<title>.+</title>')
    target_pattern=re.compile(r'<a href="[\S]+?"')
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
def collect_links(context):
    domain=context['domain']
    discovered=context['discovered']
    discovery_limit=context['discovery_limit']
    openned=context['openned']
    removed=context['removed']
    try:
        t,discovered=scrap(requests.get(domain).text,domain)
    except:
        print('Connection was reset please reconnect')
        save(context)
        sys.exit()
    d1={'title':t,'link':domain,'isinternal':True}
    openned.append(d1)
    while len(discovered)-removed>len(openned):
        for d in discovered:
            if not openned.__contains__(d):
                if d['isinternal']:
                    try:
                        data=requests.get(d['url']).text
                    except:
                        print('Connection was reset, please reconnect')
                        context={'domain':domain,'discovered':discovered,'openned':openned,'removed':removed}
                        print('Successfully saved project context')
                        save(context)
                        sys.exit()
                    t,links=scrap(data,domain)
                    if len(discovered)>discovery_limit:
                        context=context={'domain':domain,'discovered':discovered,'openned':openned,'removed':removed}
                        return context
                    for l in links:
                        if len(discovered)<discovery_limit and not discovered.__contains__(l):
                            discovered.append(l)
                    d1={'title':t,'url':d['url'],'isinternal':d['isinternal']}
                    openned.append(d1)
                else:
                    removed+=1
            if sys.platform.startswith('linux'):
                os.system('clear')
            else:
                os.system('cls')
            print(f'Discovered {len(discovered)+removed} links\t Openned {len(openned)} links\t removed {removed} noninternal links')
    return context
fs=os.listdir()
context=dict()
if fs.__contains__('harvest_context.json'):
    context=json.loads(open('harvest_context.json','r+').read())
else:
    context['domain']=input('Enter domain of the website e.g https://www.example.com\n')
    context['discovery_limit']=int(input('Enter discovery limit or 0 to discover everything\n'))
    context['discovered']=[]
    context['openned']=[]
    context['removed']=0
context=collect_links(context)
save(context)
discovered=context['discovered']
msg='<!doctype html><html><head><title>Scraped links</title></head><body><table><thead><td>Text</td><td>URL</td><td>isinternal</td></thead>'
for o in discovered:
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
else:
    context['email_server']=input('Enter email server')
    server=context['email_server']
if context.keys().__contains__('fromaddr'):
    fromaddr=context['fromaddr']
else:
    context['fromaddr']=input('Sending from:\n')
    fromaddr=context['fromaddr']
if context.keys().__contains__('toaddr'):
    toaddr=context['toaddr']
else:
    context['toaddr']=input('Sending to:\n')
    toaddr=context['toaddr']
try:
    final=SMTP(server)
except:
    save(context)
    print(f'Could not connect to {server}, please confirm that you are online')
    sys.exit()
try:
    pswd=input(f'Enter password for {fromaddr}')
    final.login(fromaddr,pswd)
except:
    save(context)
    print(f'Could not login to {fromaddr}, please confirm the login details')
    sys.exit()
try:
    final.sendmail(fromaddr,toaddr,msg)
except:
    save(context)
    print(f'Could not send email to {toaddr}, unknown error\n')
