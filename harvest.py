import json
import os
import re
import requests
import yagmail
import sys
default_configuration=b"""
{
\t"scrap":{
\t\t"domain":null,
\t\t"discovery_limit":0,
\t\t"save":{
\t\t\t"html":false,
\t\t\t"links":null
\t},
\t\t"backup/restore":null,
\t\t"output":{
\t\t\t"format":"html",
\t\t\t"file":"discovered_links"
\t\t}
\t},
\t"email":{
\t\t"send_email":false,
\t\t"sender":{
\t\t\t"password":"pass1234",
\t\t\t"email":"sender@server.com"
\t\t},
\t\t"recipients":["recipient@server.com"]
\t}
}
                    """
def write(link,data):
    path=link.removeprefix("https://")
    route=path.split("/")
    original_path=os.getcwdb()
    for i in range(len(route)-1):
        try:
            os.mkdir(route[i])
        except:
            pass
        os.chdir(route[i])
    os.chdir(original_path)

def generate_configuration_file(file_name=None):
    file_created=False
    trials=0
    if file_name!=None:
        try:
            os.remove(file_name)
            open(file_name,"x+").write(configuration)
        except:
            print(f'OverWriting original {file_name}')
            open(file_name,"x+").write(configuration)
    while not file_created:
        try:
            if trials==0:
                file_name="harvest_configuration.json"
            else:
                file_name=f"harvest_configuration({trials}).json"
            open(file_name,"x+").write(default_configuration)
            file_created=True
        except:
            trials+=1
    print(f"configuration file created as {file_name}")
            

class Harvest:
    def __init__(self,
                 configuration=None,
                 configuration_file=None,
                 domain=None,
                 discovery_limit=0,
                 save_html=False,
                 output_format=None,
                 save_links_to=None,
                 backup_to=None,
                 sender=None,
                 password=None,
                 recipients=[]
                 ):
        if configuration!=None:
            self.configuration=configuration
        elif configuration_file!=None:
            file=open(configuration_file,'x+')
            if file.read()==default_configuration:
                print(f'To use {configuration_file} please edit it first')
                sys.exit()
            self.configuration=json.loads(file.read())
        else:
            self.configuration={
	"scrap":{
		"domain":domain,
		"discovery_limit":discovery_limit,
		"save":{
			"html":save_html,
			"links":save_links_to
	},
		"backup/restore":backup_to,
		"output":{
			"format":output_format,
			"file":output_file
		}
	},
	"email":{
		"send_email":send_email,
		"sender":{
			"password":password,
			"email":sender
		},
		"recipients":recipients
	}
}
        self.title_pattern=re.compile(r"<title>.+</title>")
        self.links_pattern1=re.compile(r"https://[\S]+?")
        self.links_pattern2=re.compile(r'href="[\S]+?"')
        if self.configuration["scrap"]["backup/restore"]!=None:
            context=json.loads(open(self.configuration["backup/restore"],"r+").read())
            self.openned_links=context["openned"]
            self.opennable_links=context["discovered"]
        else:
            self.openned_links=list()
            self.opennable_links=list()
        self.get_links()
    def scrap(self,data):
        z = self.links_pattern1.findall(data)
        z.extend(self.links_pattern2.findall(data))
        d = self.title_pattern.findall(data)
        if len(d) > 0:
            t = d[0]
            t = t.removeprefix("<title>")
            t = t.removesuffix("</title>")
        else:
            t = ""
        links = []
        j = 0
        for i in z:
            if i.startswith("/"):
                z[j] = self.domain + i
            j += 1
        for i in z:
            d1 = dict()
            d1["isinternal"] = i.__contains__(self.domain)
            d1["url"] = i
            links.append(d1)
        self.opennable_links.extend(links)
        return t
    def get_context(self):
        return {"discovered_links":self.opennable_links,"openned_links":self.openned_links}
    def save(self):
        backup=self.configuration["scrap"]["backup/restore"]
        if backup!=None:
            try:
                os.remove(backup)
            except:
                print(f"Creating backup {backup}")
            open(backup, "x+").write(json.dumps(self.get_context()))
    def get_discovered_links(self):
        return self.discovered
    def get_links(self):
        if len(self.opennable_links)>self.configuration["scrap"]["discovery_limit"]:
            return
        try:
            data=requests.get(self.domain).text
            title=self.scrap(data)
            if save_html==True:
                write(self.domain,data)
            openned_link = {"title": title, "link": self.domain, "isinternal": True}
            self.openned_links.append(openned_link)
        except:
            print("Connection was reset please reconnect")
            self.save()
            print("Scraping context saved at harvest_context.json")
            sys.exit()
        
        for i in range(len(self.opennable_links)):
            try:
                if self.openned_links.__contains__(self.opennable_links[i]):
                    data=requests.get(self.opennable_links[i]).text
                    title=self.scrap(requests.get(data))
                    if save_html:
                        write(self.opennable_links[i],data)
                    openned_link=self.opennable_links[i]
                    openned_link["title"]=title
                    self.openned_links.append(openned_link)
            except:
                save()
                print("Connection was please reconnect")
            if len(self.opennable_links)>self.discovery_limit:
                self.save()
                if self.configuration['email']['send_email']:
                    self.send_email()
    def generate_json(self):
        return json.dumps({"discovered":self.discovered,"openned":self.openned})
    def generate_html(self):
        msg = "<!doctype html><html><head><title>Scraped links</title></head><body><table><thead><td>Text</td><td>URL</td><td>isinternal</td></thead>"
        for o in self.discovered:
            try:
                msg += "<tr><td>" + o["title"] + "</td>"
            except:
                msg += "<tr><td>No title</td>"
            msg += "<td>" + o["url"] + "</td>"
            msg += "<td>" + str(o["isinternal"]) + "</td></tr>"
        msg += "</table></body></html>"
        return msg
    def get_output(self):
        '''
Returns the output of the scraping process in the format specified in the configuration
        '''
        _format=self.configuration['scrap']['output']['format']
        if _format=='json':
            return self.generate_json()
        elif _format=="html":
            return self.generate_html
        else:
            return self.context
    def send_email(self):
        yag=yagmail.SMTP(self.configuration['email']["sender"]['email'],self.configuration['email']['sender']["passwd"])
        subject="Scraped links"
        attachment=["harvested_links.html"]
        yag.send(to=configuration["recipients"],subject=subject,attachments=attachment)
        yag.close()
if __name__=="__main__":
    if sys.argv[1]=="generate-config":
        generate_configuration_file()
    elif sys.argv[1]=="scrap":
        if len(sys.argv)>2:
            context=Harvest(configuration_file=sys.argv[2])
        else:
            context=Harvest(configuration_file='harvest_configuration.json')
