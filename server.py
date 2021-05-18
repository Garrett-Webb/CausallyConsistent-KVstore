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

        if "/key-value-store-view" in str(self.path) and self.client_address[0] + ":8085" in views_list: # self.client_address[0] = ip, view_list = ip + :port
            print("key-value-store-view")
            down_instances = []

            for x in views_list:
                try:
                    if x != saddr:
                        r = requests.get('http://' + x + "/key-value-store/check", headers=self.headers)
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
                      r = requests.delete('http://' + x + "/broadcast-view-delete", allow_redirects=False, headers=self.headers, json={"socket-address" : y})

            self._set_headers(response_code=200)
            response = bytes(json.dumps({"message" : "View retrieved successfully", "view" : ','.join(views_list) }), 'utf-8')
            self.wfile.write(response)

        elif "/key-value-store/" in str(self.path):
                keystr = str(self.path).split("/key-value-store/",1)[1]
                if(len(keystr) > 0 and len(keystr) < 50):
                    if keystr in kvstore:
                        self._set_headers(response_code=200)
                        response = bytes(json.dumps({"doesExist" : True, "message" : "Retrieved successfully", "value" : kvstore[keystr]}), 'utf-8')
                    else:
                        self._set_headers(response_code=404)
                        response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in GET"}), 'utf-8')
                elif (len(keystr) > 50):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in GET"}), 'utf-8')
                elif(len(keystr) == 0):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in GET"}), 'utf-8')
                self.wfile.write(response)
        
        else:
            #default 500 code to clean up loose ends
            self._set_headers(response_code=500)
        return

    def do_PUT(self):
        if "/key-value-store-view" in str(self.path) and self.client_address[0] + ":8085" in views_list: # self.client_address[0] = ip, view_list = ip + :port
            #in progress
            print("Content length" + self.headers['Content-Length'])
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            new_string = self.data_string.decode()
            new_string = new_string.replace('{', '')
            new_string = new_string.replace('}', '')
            new_instance = new_string.split(": ")[1]
            print("NEW INSTANCE: " + str(new_instance))

            if new_instance not in views_list:
                views_list.append(new_instance)
                print(views_list)

                #send PUT to all replicas

                self._set_headers(response_code=201) 
                response = bytes(json.dumps({'message' : "Replica added successfully to the view"}), 'utf-8')
                self.wfile.write(response)
            else:
                #error
                self._set_headers(response_code=404)
                response = bytes(json.dumps({'error' : "Socket address already exists in the view", "message" : "Error in PUT"}), 'utf-8')
                self.wfile.write(response)
                
            

            

        else:
            if "/key-value-store/" in str(self.path):
                keystr = str(self.path).split("/key-value-store/",1)[1]
                if(len(keystr) > 0 and len(keystr) < 50):
                    self.data_string = self.rfile.read(int(self.headers['Content-Length']))
                    data = json.loads(self.data_string)
                    if "value" not in data:
                        self._set_headers(response_code=400)
                        response = bytes(json.dumps({'error' : "Value is missing", 'message' : "Error in PUT"}), 'utf-8')
                    elif keystr in kvstore:
                        kvstore[keystr] = data["value"]
                        self._set_headers(response_code=200)
                        response = bytes(json.dumps({'message' : "Updated successfully", 'replaced' :True}), 'utf-8')
                    else:
                        kvstore[keystr] = data["value"]
                        self._set_headers(response_code=201)
                        response = bytes(json.dumps({'message' : "Added successfully", 'replaced' :False}), 'utf-8')
                elif (len(keystr) > 50):
                    self._set_headers(response_code=400)
                    response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in PUT"}), 'utf-8')
                
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
                response = bytes(json.dumps({"bogus" : "doesnt matter", "message" : "done"}), 'utf-8')
                self.wfile.write(response)
                return

            views_list.remove(delete_replica)
            print("View_list (after delete): ")
            print(views_list)
            
            self._set_headers(response_code=200)
            response = bytes(json.dumps({"bogus" : "doesnt matter", "message" : "done"}), 'utf-8')
            self.wfile.write(response)

        elif "/key-value-store-view" in str(self.path): # self.client_address[0] = ip, view_list = ip + :port
            print("view delete: ")
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            new_string = self.data_string.decode()
            new_string = new_string.replace('{', '')
            new_string = new_string.replace('}', '')
            delete_replica = new_string.split(": ")[1]
            print(delete_replica)
            if delete_replica not in views_list:
                self._set_headers(response_code=404)
                response = bytes(json.dumps({"error" : "Socket address does not exist in the view", "message" : "Error in DELETE"}), 'utf-8')
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
                                r = requests.delete('http://' + y + "/broadcast-view-delete" , allow_redirects = False, headers=self.headers, json={"socket-address" : delete_replica})
                else:
                    print("Cannot send request to self")
                print(views_list)
                
            self._set_headers(response_code=200)
            self.end_headers()
            response = bytes(json.dumps({'message' : "Replica deleted successfully from the view"}), 'utf-8')
            self.wfile.write(response)

        elif "/key-value-store/" in str(self.path):
            keystr = str(self.path).split("/key-value-store/",1)[1]
            if(len(keystr) > 0 and len(keystr) < 50):
                if keystr in kvstore:
                    del kvstore[keystr]
                    self._set_headers(response_code=200)
                    response = bytes(json.dumps({"doesExist" : True, "message" : "Deleted successfully"}), 'utf-8')
                else:
                    self._set_headers(response_code=404)
                    response = bytes(json.dumps({"doesExist" : False, "error" : "Key does not exist", "message" : "Error in DELETE"}), 'utf-8')
            elif (len(keystr) > 50):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key is too long", 'message' : "Error in DELETE"}), 'utf-8')
            elif(len(keystr) == 0):
                self._set_headers(response_code=400)
                response = bytes(json.dumps({'error' : "Key not specified", 'message' : "Error in DELETE"}), 'utf-8')
            self.wfile.write(response)
        
        else:
            #default 500 code to clean up loose ends
            self._set_headers(response_code=500)
        return

def run(server_class=http.server.HTTPServer, handler_class=requestHandler, addr='0.0.0.0', port=8085):
    # this function initializes and runs the server on the class defined above
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)
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