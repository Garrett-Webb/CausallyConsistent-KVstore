# server.py

# Assignment 2
# CruzIDs
# Garrett Webb: gswebb
# Kai Hsieh: kahsieh
# Rahul Arora: raarora

#CSE138 Kuper Spring 2021

#acknowledgements
#https://stackabuse.com/serving-files-with-pythons-simplehttpserver-module/
#https://docs.python.org/3/library/http.server.html
#https://stackoverflow.com/questions/31371166/reading-json-from-simplehttpserver-post-data
#https://realpython.com/python-requests/#headers

import requests
import sys
import http.server
import socketserver
import json
from sys import argv
import os
kvstore = {}
main_flag = False
saddr = ""
views = ""
views_list = []

class requestHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, response_code):
        self.send_response(response_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        print("GET REQUEST RECEIVED")

        if "/key-value-store-view" in str(self.path):#and self.client_address[0] + ":8085" in views_list: # self.client_address[0] = ip, view_list = ip + :port
            print("key-value-store-view")
            down_instances = []

            for x in views_list:
                try:
                    if x != saddr:
                        r = requests.get('http://' + x + "/key-value-store/check", timeout=3, headers=self.headers)
                except:
                    down_instances.append(x)
                    views_list.remove(x)
            print("Down Instances:\n")
            print(down_instances)
            print("Views List:\n")
            print(views_list)


            for x in views_list:
                if (x not in down_instances) and (x != saddr):
                    for y in down_instances:
                        try:
                            r = requests.delete('http://' + x + "/broadcast-view-delete", timeout=3, allow_redirects=False, headers=self.headers, json={"socket-address" : y})
                        except:
                            print("instance ", + y + " is also down lol")

            self._set_headers(response_code=200)
            response = bytes(json.dumps({"message" : "View retrieved successfully", "view" : ','.join(views_list), "causal-metadata":"" }), 'utf-8')
            self.wfile.write(response)

            
        elif "/update-kv-store" in str(self.path):#and self.client_address[0] + ":8085" in views_list: # self.client_address[0] = ip, view_list = ip + :port
            print("update-kv-store")
            
            json_thing = json.dumps(kvstore)
            print(json_thing)
            

            self._set_headers(response_code=200)
            response = bytes(json.dumps(kvstore), 'utf-8')
            self.wfile.write(response)
        
        
        elif "/key-value-store/" in str(self.path):
                keystr = str(self.path).split("/key-value-store/",1)[1]
                if(len(keystr) > 0 and len(keystr) < 50):
                    if keystr in kvstore:
                        self._set_headers(response_code=200)
                        response = bytes(json.dumps({"doesExist" : True, "message" : "Retrieved successfully", "value" : kvstore[keystr], "causal-metadata":"test"}), 'utf-8')
                    else:
                        self._set_headers(response_code=404)
                        response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in GET", "causal-metadata":"test"}), 'utf-8')
                elif (len(keystr) > 50):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in GET", "causal-metadata":"test"}), 'utf-8')
                elif(len(keystr) == 0):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in GET", "causal-metadata":"test"}), 'utf-8')
                self.wfile.write(response)
        
        else:
            #default 500 code to clean up loose ends
            self._set_headers(response_code=500)
        return

    def do_PUT(self):
        if "/broadcast-view-put" in str(self.path):
            print("broadcasted PUT: ")
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            new_string = self.data_string.decode()
            new_string = new_string.replace('{', '')
            new_string = new_string.replace('}', '')
            new_string = new_string.replace('"', '')
            new_string = new_string.split(": ")[1]
            print("View_list (before put): ")
            print(views_list)

            if new_string in views_list:
                print("view already in views_list")
                self._set_headers(response_code=404)
                response = bytes(json.dumps({"bogus" : "doesnt matter", "message" : "done", "causal-metadata":"test"}), 'utf-8')
                self.wfile.write(response)
                return

            views_list.append(new_string)
            print("View_list (after put): ")
            print(views_list)
            
            self._set_headers(response_code=200)
            response = bytes(json.dumps({"bogus" : "doesnt matter", "message" : "done", "causal-metadata":"test"}), 'utf-8')
            self.wfile.write(response)
            return
        
        elif "/key-value-store-view" in str(self.path): #and self.client_address[0] + ":8085" in views_list: # self.client_address[0] = ip, view_list = ip + :port
            #in progress
            print("Content length" + self.headers['Content-Length'])
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            new_string = self.data_string.decode()
            new_string = new_string.replace('{', '')
            new_string = new_string.replace('}', '')
            new_instance = new_string.split(": ")[1]
            print("NEW INSTANCE: " + str(new_instance))

            if new_instance not in views_list:
                print("Views List (before PUT)", views_list)

                #send PUT to all replicas
                for x in views_list:
                    if (x != saddr):
                        try:
                            print("TRY: broadcasting PUT value ", new_instance, "to ", x)
                            r = requests.put('http://' + x + "/broadcast-view-put", timeout=3, allow_redirects=False, headers=self.headers, json={"socket-address" : new_instance})
                        except:
                            print("EXCEPT: removing PUT value ", x, "from ", saddr)
                            views_list.remove(x)
                            for y in views_list:
                                print("Broadcasting DELETE downed instance ", x, "to ", y)
                                if (y != saddr) and (y != x):
                                    try:
                                        r = requests.delete('http://' + y + "/broadcast-view-delete", timeout=3, allow_redirects=False, headers=self.headers, json={"socket-address" : x})
                                    except:
                                        print("broadcasting instance is down")

                views_list.append(new_instance)
                print("Views List (after PUT)", views_list)
                self._set_headers(response_code=201) 
                response = bytes(json.dumps({'message' : "Replica added successfully to the view", "causal-metadata":"test"}), 'utf-8')
                self.wfile.write(response)
            else:
                #error
                self._set_headers(response_code=404)
                response = bytes(json.dumps({'error' : "Socket address already exists in the view", "message" : "Error in PUT", "causal-metadata":"test"}), 'utf-8')
                self.wfile.write(response)
      
        elif "/broadcast-key-put/" in str(self.path):
            print("in broadcast key put \n")
            keystr = str(self.path).split("/broadcast-key-put/",1)[1]
            if(len(keystr) > 0 and len(keystr) < 50):
                self.data_string = self.rfile.read(int(self.headers['Content-Length']))
                data = json.loads(self.data_string)
                if "value" not in data:
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Value is missing", 'message' : "Error in PUT", "causal-metadata":"test"}), 'utf-8')
                elif keystr in kvstore:
                    kvstore[keystr] = data["value"]
                    self._set_headers(response_code=200)
                    response = bytes(json.dumps({'message' : "Updated successfully", 'replaced' :True, "causal-metadata":"test"}), 'utf-8')
                else:
                    kvstore[keystr] = data["value"]
                    self._set_headers(response_code=201)
                    response = bytes(json.dumps({'message' : "Added successfully", 'replaced' :False, "causal-metadata":"test"}), 'utf-8')
            elif (len(keystr) > 50):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in PUT", "causal-metadata":"test"}), 'utf-8')
                
            self.wfile.write(response)

        else:
            if "/key-value-store/" in str(self.path):
                keystr = str(self.path).split("/key-value-store/",1)[1]
                if(len(keystr) > 0 and len(keystr) < 50):
                    self.data_string = self.rfile.read(int(self.headers['Content-Length']))
                    data = json.loads(self.data_string)
                    if "value" not in data:
                        self._set_headers(response_code=400)
                        response = bytes(json.dumps({'error' : "Value is missing", 'message' : "Error in PUT", "causal-metadata":"test"}), 'utf-8')
                    elif keystr in kvstore:
                        kvstore[keystr] = data["value"]
                        # Send key PUT to all other replicas
                        for replica in views_list:
                            print("ENTER FOR LOOP\n")
                            if (replica != saddr):
                                print("REPLICA IS " + str(replica) + "\n")
                                print("saddr is" + str(saddr) + "\n")
                                try:
                                    print("Broadcasting PUT value ", str(keystr), " to ", str(replica))
                                    r = requests.put('http://' + replica + "/broadcast-key-put/" + keystr, timeout=3, allow_redirects=False, headers=self.headers, json={"value" : data["value"], "causal-metadata": data["causal-metadata"]})
                                except:
                                    print("The instance is down, broadcasting delete view to all up instances")
                                    views_list.remove(replica)
                                    # self._set_headers(response_code=500)
                                    # response = bytes(json.dumps({'message' : "Uh oh stinky", "causal-metadata":"test"}), 'utf-8')
                                    # self.wfile.write(response)
                                    # return
                                    for y in views_list:
                                        print("Broadcasting DELETE downed instance ", replica, "to ", y)
                                        if (y != saddr) and (y != replica):
                                            try:
                                                r = requests.put('http://' + y + "/broadcast-view-delete", timeout=3, allow_redirects=False, headers=self.headers, json={"socket-address" : replica})
                                            except:
                                                print("instance is also down")
                        self._set_headers(response_code=200)
                        response = bytes(json.dumps({'message' : "Updated successfully", 'replaced' :True, "causal-metadata":"test"}), 'utf-8')
                        self.wfile.write(response)
                        return
                    else:
                        kvstore[keystr] = data["value"]
                        # Send key PUT to all other replicas
                        for replica in views_list:
                            print("ENTER FOR LOOP\n")
                            if (replica != saddr):
                                try:
                                    print("Broadcasting PUT value ", str(keystr), " to ", str(replica))
                                    r = requests.put('http://' + replica + "/broadcast-key-put/" + keystr, timeout=3, allow_redirects=False, headers=self.headers, json={"value" : data["value"], "causal-metadata": data["causal-metadata"]})
                                except:
                                    print("The instance is down, broadcasting delete view to all up instances")
                                    for y in views_list:
                                        print("Broadcasting DELETE downed instance ", replica, "to ", y)
                                        if (y != saddr) and (y != replica):
                                            try:
                                                r = requests.put('http://' + y + "/broadcast-view-delete", allow_redirects=False, headers=self.headers, json={"socket-address" : replica})
                                            except:
                                                print("instance is also down")
                        self._set_headers(response_code=201)
                        response = bytes(json.dumps({'message' : "Added successfully", 'replaced' :False, "causal-metadata":"test"}), 'utf-8')
                        self.wfile.write(response)
                        return
                elif (len(keystr) > 50):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in PUT", "causal-metadata":"test"}), 'utf-8')
                
                self.wfile.write(response)
            else:
                self._set_headers(response_code=500)
        return
    
    def do_DELETE(self):

        print(self.client_address[0])
        # print(views_list[2])

        view_list_str = []
        for x in views_list:
            view_list_str.append(str(x))

        if "/broadcast-view-delete" in str(self.path):
            print("broadcasted delete: ")
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            new_string = self.data_string.decode()
            new_string = new_string.replace('{', '')
            new_string = new_string.replace('}', '')
            new_string = new_string.replace('"', '')
            delete_replica = new_string.split(": ")[1]
            print("View_list (before delete): ")
            print(view_list_str)

            if delete_replica.strip() not in view_list_str:
                print("view not in views_list")
                self._set_headers(response_code=200)
                response = bytes(json.dumps({"bogus" : "doesnt matter", "message" : "done", "causal-metadata":"test"}), 'utf-8')
                self.wfile.write(response)
                return

            views_list.remove(delete_replica)
            print("View_list (after delete): ")
            print(views_list)
            
            self._set_headers(response_code=200)
            response = bytes(json.dumps({"bogus" : "doesnt matter", "message" : "done", "causal-metadata":"test"}), 'utf-8')
            self.wfile.write(response)

        elif "/broadcast-key-delete" in str(self.path):
            print("broadcasted key delete: ")
            keystr = str(self.path).split("/broadcast-key-delete/",1)[1]
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(self.data_string)
            c_meta = data["causal-metadata"]
            print("Causal Metadata:", str(c_meta))
            if(len(keystr) > 0 and len(keystr) < 50):
                if keystr in kvstore:
                    del kvstore[keystr]
                    self._set_headers(response_code=200)
                    response = bytes(json.dumps({"message" : "Deleted successfully", "causal-metadata":"test"}), 'utf-8')
                else:
                    self._set_headers(response_code=404)
                    response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
            elif (len(keystr) > 50):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
            elif(len(keystr) == 0):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
            self.wfile.write(response)

        elif "/key-value-store-view" in str(self.path): # self.client_address[0] = ip, view_list = ip + :port
            print("view delete: ")
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(self.data_string)
            new_string = self.data_string.decode()
            new_string = new_string.replace('{', '')
            new_string = new_string.replace('}', '')
            delete_replica = new_string.split(": ")[1]
            print(delete_replica)
            if delete_replica not in views_list:
                self._set_headers(response_code=404)
                response = bytes(json.dumps({"error" : "Socket address does not exist in the view", "message" : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
                self.wfile.write(response)
                return
            print("View_list (before delete): ", views_list)
            views_list.remove(delete_replica)
            print("View_list: ", views_list)

            #send delete to all other replicas in the view lsit
            for x in views_list:
                if x != saddr:
                    try:
                        print( "TRY: deleting ", str(delete_replica), " at ", str(x) )
                        r = requests.delete('http://' + x + "/broadcast-view-delete", allow_redirects=False, headers=self.headers, json={"socket-address" : delete_replica})
                    except:
                        for y in views_list:
                            print( "EXCEPT: broadcasting delete of ", str(x), " at ", str(y) )  
                            if (self.client_address[0] + ":8085" != y) and (x != y):
                                try:
                                    r = requests.delete('http://' + y + "/broadcast-view-delete" , allow_redirects = False, headers=self.headers, json={"socket-address" : delete_replica})
                                except:
                                    print("instance is also down")
                else:
                    print("Cannot send request to self")
                print(views_list)
                
            self._set_headers(response_code=200)
            self.end_headers()
            response = bytes(json.dumps({'message' : "Replica deleted successfully from the view", "causal-metadata":"test"}), 'utf-8')
            self.wfile.write(response)

        elif "/key-value-store/" in str(self.path):
            keystr = str(self.path).split("/key-value-store/",1)[1]
            if(len(keystr) > 0 and len(keystr) < 50):
                if keystr in kvstore:
                    # Send key DELETE to all other replicas
                    for replica in views_list:
                        if (replica != saddr):
                            try:
                                print("Broadcasting DELETE key value ", str(keystr), " to ", str(replica))
                                r = requests.delete('http://' + replica + "/broadcast-key-delete/" + keystr, allow_redirects=False, headers=self.headers, json={"causal-metadata": "test"})
                            except:
                                print("The instance is down, broadcasting delete view to all up instances")
                                views_list.remove(replica)
                                for y in views_list:
                                    print("Broadcasting DELETE downed instance ", replica, "to ", y)
                                    if (y != saddr) and (y != replica):
                                        try:
                                            r = requests.delete('http://' + y + "/broadcast-view-delete", allow_redirects=False, headers=self.headers, json={"socket-address" : replica})
                                        except:
                                            print("instance is also down")
                    del kvstore[keystr]
                    self._set_headers(response_code=200)
                    response = bytes(json.dumps({"message" : "Deleted successfully", "causal-metadata":"test"}), 'utf-8')
                    
                    
                else:
                    self._set_headers(response_code=404)
                    response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
            elif (len(keystr) > 50):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
            elif(len(keystr) == 0):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in DELETE", "causal-metadata":"test"}), 'utf-8')
            self.wfile.write(response)
         
        else:
            #default 500 code to clean up loose ends
            self._set_headers(response_code=500)
        return

def run(server_class=http.server.HTTPServer, handler_class=requestHandler, addr='0.0.0.0', port=8085):
    # this function initializes and runs the server on the class defined above
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
    for replica in views_list:
        if replica != saddr:
            try:
                r = requests.put('http://' + replica + "/broadcast-view-put", timeout=2, allow_redirects=False, json={"socket-address" : saddr})
            except:
                print("replica ", replica, " in view is not yet live.")
    for replica in views_list:
        if replica != saddr:
            print("requesting http://" + replica + "/update-kv-store")
            try:
                r = requests.get('http://'+ replica + "/update-kv-store", timeout=2)
                response_json = r.json()
                print(type(response_json))
                for key in response_json:
                    kvstore[key] = response_json[key]
                #kvstore = response_json
                print("kvstore is as follows:")
                print(kvstore)
                print("kvstore type is:")
                print(type(kvstore))
                break
            except:
                print("replica is not up yet")
    print(f"Starting HTTP server on {addr}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == '__main__':
    d_ip = ''
    d_port = 8085
    try:
        saddr = os.environ['SOCKET_ADDRESS']
        if len(saddr) > 0:
            print("SOCKET_ADDRESS: " + str(saddr))
        views = os.environ['VIEW']
        views_list = views.split(",")
        if len(saddr) > 0:
            print("VIEWS: " + str(views))

    except:
        print("main instance")
        main_flag = True
        
    print(main_flag)
    x = 0
    for arg in argv:
        print("arg" + str(x) + ": " + str(argv[x]))
        x = x+1

    if len(argv) == 2:
        #call the run function with custom port
        run(port=int(argv[1]))
    else:
        #call the run function with default port 8085
        #addr_s, saddr_port = saddr.split(":")
        run()